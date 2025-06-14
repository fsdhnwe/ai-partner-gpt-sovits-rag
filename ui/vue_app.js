const { createApp } = Vue;

createApp({
    data() {
        return {
            currentView: 'chat',
            userInput: '',
            messages: [],
            isTyping: false,
            isOnline: false,
            currentModel: 'deepseek-r1:latest',
            messageId: 0,
            
            // 設定資料            
            settings: {
                llmModel: 'deepseek-r1:latest',
                apiUrl: 'http://localhost:8000',
                referenceAudio: 'GPT-SoVITS-0601-cu124/custom_refs/base-audio.wav',
                gptModelPath: 'GPT-SoVITS-0601-cu124/GPT_weights_v2/wednesday.ckpt',
                sovitsModelPath: 'GPT-SoVITS-0601-cu124/SoVITS_weights_v2/wednesday.pth',
                outputPath: 'output',  // 新增：音頻輸出路徑
                autoPlayAudio: true,
                documentsPath: 'scripts',
                vectorDbPath: 'db'
            }
        }
    },

    mounted() {
        this.loadSettings();
        this.checkConnection();
        this.addWelcomeMessage();
    },

    methods: {
        // 聊天功能
        async sendMessage() {
            if (!this.userInput.trim() || this.isTyping) return;

            const userMessage = {
                id: this.messageId++,
                type: 'user',
                content: this.userInput,
                timestamp: new Date()
            };

            this.messages.push(userMessage);
            const inputText = this.userInput;
            this.userInput = '';
            this.isTyping = true;

            this.scrollToBottom();

            try {
                const response = await this.callChatAPI(inputText);
                
                const assistantMessage = {
                    id: this.messageId++,
                    type: 'assistant',
                    content: response.message,
                    audioPath: response.audio_path,
                    audioStatus: response.tts_status || 'ready',
                    timestamp: new Date()
                };

                this.messages.push(assistantMessage);
                
                // 如果音頻正在生成中，開始檢查狀態
                if (assistantMessage.audioStatus === 'generating' && response.audio_path) {
                    this.checkAudioStatus(assistantMessage, response.audio_path);
                }
                
                // 自動播放語音（如果已準備好）
                if (this.settings.autoPlayAudio && response.audio_path && assistantMessage.audioStatus === 'ready') {
                    setTimeout(() => {
                        this.playAudio(response.audio_path);
                    }, 500);
                }

            } catch (error) {
                console.error('聊天 API 錯誤:', error);
                
                const errorMessage = {
                    id: this.messageId++,
                    type: 'assistant',
                    content: '抱歉，我遇到了一些技術問題。請稍後再試。',
                    timestamp: new Date()
                };
                
                this.messages.push(errorMessage);
            } finally {
                this.isTyping = false;
                this.scrollToBottom();
            }
        },

        async callChatAPI(message) {
            const response = await axios.post(`${this.settings.apiUrl}/chat`, {
                message: message,
                use_tts: this.settings.autoPlayAudio,
                model: this.settings.llmModel,
                output_path: this.settings.outputPath
            }, {
                timeout: 30000
            });

            return response.data;
        },

        // 播放音頻
        playAudio(audioPath) {
            if (!audioPath) return;

            try {
                // 只使用文件名部分，移除任何路徑
                const filename = audioPath.split(/[/\\]/).pop();
                const audio = new Audio(`${this.settings.apiUrl}/audio/${encodeURIComponent(filename)}`);
                audio.play().catch(error => {
                    console.error('音頻播放失敗:', error);
                });
            } catch (error) {
                console.error('音頻載入失敗:', error);
            }
        },

        // 滾動到底部
        scrollToBottom() {
            this.$nextTick(() => {
                const container = this.$refs.messagesContainer;
                if (container) {
                    container.scrollTop = container.scrollHeight;
                }
            });
        },

        // 檢查連線狀態
        async checkConnection() {
            console.log('正在檢查 API 連線狀態...');
            try {
                const response = await axios.get(`${this.settings.apiUrl}/health`, {
                    timeout: 5000
                });
                console.log('API 回應:', response.data);
                
                // 檢查 Ollama 狀態
                this.isOnline = response.data.ollama_status === 'online';
                if (this.isOnline) {
                    this.currentModel = response.data.model || this.settings.llmModel;
                    this.showNotification('已連線到 API 和 Ollama 服務', 'success');
                } else {
                    this.showNotification('Ollama 服務未啟動', 'warning');
                }
                
            } catch (error) {
                this.isOnline = false;
                console.error('API 連線失敗:', error.message);
                if (error.code === 'ECONNREFUSED') {
                    this.showNotification('無法連接到 API 服務，請確認服務是否啟動', 'error');
                } else {
                    this.showNotification(`API 連線錯誤: ${error.message}`, 'error');
                }
            }
        },

        // 新增歡迎訊息
        addWelcomeMessage() {
            const welcomeMessage = {
                id: this.messageId++,
                type: 'assistant',
                content: '我是 Wednesday Addams，一個喜歡黑暗和詩意的 AI 助手。有什麼我可以幫助你的嗎？',
                timestamp: new Date()
            };
            
            this.messages.push(welcomeMessage);
        },

        // 設定管理
        saveSettings() {
            try {
                localStorage.setItem('wednesday_settings', JSON.stringify(this.settings));
                this.showNotification('設定已儲存', 'success');
                this.checkConnection(); // 重新檢查連線
            } catch (error) {
                this.showNotification('儲存設定失敗', 'error');
                console.error('儲存設定錯誤:', error);
            }
        },

        loadSettings() {
            try {
                const saved = localStorage.getItem('wednesday_settings');
                if (saved) {
                    this.settings = { ...this.settings, ...JSON.parse(saved) };
                    this.currentModel = this.settings.llmModel;
                }
            } catch (error) {
                console.error('載入設定錯誤:', error);
            }
        },

        async rebuildDatabase() {
            if (!confirm('確定要重建向量資料庫嗎？這可能需要一些時間。')) {
                return;
            }

            try {
                this.showNotification('正在重建資料庫...', 'info');
                
                const response = await axios.post(`${this.settings.apiUrl}/rebuild-db`, {
                    documents_path: this.settings.documentsPath
                }, {
                    timeout: 120000 // 2分鐘超時
                });

                if (response.status === 200) {
                    this.showNotification('資料庫重建完成', 'success');
                } else {
                    throw new Error('重建失敗');
                }
            } catch (error) {
                this.showNotification('資料庫重建失敗', 'error');
                console.error('重建資料庫錯誤:', error);
            }
        },

        // 通知系統
        showNotification(message, type = 'info') {
            // 簡單的通知實現
            const notification = document.createElement('div');
            notification.className = `notification notification-${type}`;
            notification.textContent = message;
            
            notification.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                padding: 12px 24px;
                border-radius: 8px;
                color: white;
                font-weight: 500;
                z-index: 1000;
                animation: slideIn 0.3s ease;
                ${type === 'success' ? 'background: #10b981;' : ''}
                ${type === 'error' ? 'background: #ef4444;' : ''}
                ${type === 'info' ? 'background: #3b82f6;' : ''}
            `;

            document.body.appendChild(notification);

            setTimeout(() => {
                notification.style.animation = 'slideOut 0.3s ease';
                setTimeout(() => {
                    document.body.removeChild(notification);
                }, 300);
            }, 3000);
        },

        // 格式化時間
        formatTime(date) {
            return new Intl.DateTimeFormat('zh-TW', {
                hour: '2-digit',
                minute: '2-digit'
            }).format(date);
        },        async checkAudioStatus(message, audioPath) {
            let attempts = 0;
            const maxAttempts = 100; // 最多檢查100次（100秒）
            
            const checkStatus = async () => {
                try {
                    // 只使用文件名部分，移除任何路徑
                    const filename = audioPath.split(/[/\\]/).pop();
                    console.log('檢查音頻狀態:', filename);
                    
                    const response = await axios.get(`${this.settings.apiUrl}/audio_status/${encodeURIComponent(filename)}`);
                    
                    if (response.data.status === 'ready') {
                        // 音頻已準備好
                        message.audioStatus = 'ready';
                        message.audioPath = filename; // 只保留檔名
                        
                        // 自動播放（如果設置了）
                        if (this.settings.autoPlayAudio) {
                            setTimeout(() => {
                                this.playAudio(filename);
                            }, 500);
                        }
                        
                        console.log('✅ 音頻已準備就緒:', filename);
                        return;
                    }
                    
                    attempts++;
                    if (attempts < maxAttempts) {
                        // 繼續檢查
                        setTimeout(checkStatus, 1000);
                    } else {
                        // 超時
                        message.audioStatus = 'timeout';
                        console.warn('⚠️ 音頻生成超時:', filename);
                    }
                    
                } catch (error) {
                    console.error('檢查音頻狀態失敗:', error);
                    if (error.response && error.response.status === 404) {
                        // 如果文件不存在，继续等待
                        attempts++;
                        if (attempts < maxAttempts) {
                            setTimeout(checkStatus, 1000);
                            return;
                        }
                    }
                    message.audioStatus = 'error';
                }
            };
            
            // 開始檢查
            setTimeout(checkStatus, 1000);
        },

        getAudioButtonTitle(status) {
            switch(status) {
                case 'generating':
                    return '語音生成中...';
                case 'ready':
                    return '播放語音';
                case 'timeout':
                    return '語音生成超時';
                case 'error':
                    return '語音生成失敗';
                default:
                    return '播放語音';
            }
        },

        // ...existing code...
    },

    // 定期檢查連線狀態
    created() {
        setInterval(() => {
            this.checkConnection();
        }, 30000); // 每30秒檢查一次
    }
}).mount('#app');

// 新增 CSS 動畫
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }

    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);

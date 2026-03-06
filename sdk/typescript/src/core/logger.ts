export const logger = {
    info: (msg: string, meta?: any) => {
        console.log(JSON.stringify({ timestamp: new Date().toISOString(), level: 'INFO', event: msg, ...meta }));
    },
    debug: (msg: string, meta?: any) => {
        if (process.env.DETERMINAI_LOG_LEVEL === 'DEBUG') {
            console.log(JSON.stringify({ timestamp: new Date().toISOString(), level: 'DEBUG', event: msg, ...meta }));
        }
    },
    error: (msg: string, meta?: any) => {
        console.error(JSON.stringify({ timestamp: new Date().toISOString(), level: 'ERROR', event: msg, ...meta }));
    }
};

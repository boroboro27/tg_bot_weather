
""" Словарь с конфигурацией для логирования """

LOGGING_CONFIG = { 
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': { 
        'standard': { 
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
    },
    'handlers': { 
        'console': { 
            'level': 'DEBUG',
            'formatter': 'standard',
            'class': 'logging.StreamHandler',                        
            'stream': 'ext://sys.stdout',  # Default is stderr
        },
        'file': { 
            'level': 'INFO',
            'formatter': 'standard', 
            'class': 'logging.FileHandler',                       
            'filename': 'bot.log',
            'encoding': 'utf-8'
        },
    },
    'loggers': { 
        '': {  # root logger
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False
        },
        'my.packg': { 
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False
        },
        '__main__': {  # if __name__ == '__main__'
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False
        },
    } 
}
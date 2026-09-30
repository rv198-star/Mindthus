"""Owner-selected defaults for new CLI runs; frozen runs retain their identity."""

HOST_MODEL = 'gpt-6.1-sol'
HOST_EFFORT = 'xhigh'


def host_configuration():
    return {'model': HOST_MODEL, 'reasoning_effort': HOST_EFFORT,
            'transport_profile': 'mindthus_official_http'}

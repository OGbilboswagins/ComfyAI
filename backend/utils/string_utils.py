def error_format(e: Exception) -> str:
    error_message = str(e).replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
    # 移除可能导致JSON解析错误的控制字符
    error_message = ''.join(char for char in error_message if ord(char) >= 32 or char in '\n\r\t')
    return error_message
_commands = {}


def command(aliases=None, permission_level: int = 0, is_command: bool = True,
            need_check_exclude: bool = False):
    """
        创建一条命令，主指令名为函数名。

        :param aliases: 指令的别名，默认为空。
        :param permission_level: 执行需要的权限等级，默认为0都可执行，1代表至少是mod，2代表至少是admin
        :param is_command: 代表该条指令需不需要前置/
        :param need_check_exclude: 代表该条指令是否需要检查群号白名单
    """

    if aliases is None:
        aliases = []

    def decorator(func):
        command_name = func.__name__

        _commands[f'/{command_name}' if is_command else f'{command_name}'] = (
            func, permission_level, is_command, need_check_exclude)
        for alias in aliases:
            _commands[f'/{alias}' if is_command else f'{alias}'] = (
                func, permission_level, is_command, need_check_exclude)
        return func

    return decorator

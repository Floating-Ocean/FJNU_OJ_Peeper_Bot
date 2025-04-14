def register_all_modules():
    from .atc import register_module
    from .cf import register_module
    from .color_rand import register_module
    from .contest_manual import register_module
    from .nk import register_module
    from .peeper import register_module
    from .pick_one import register_module
    from .rand import register_module
    from .uptime import register_module

    register_module()

register_all_modules()

def register(ctx):
    ctx.register_command(name="wright", description="Wright fixture command", handler=lambda *_args, **_kwargs: "ok")

from flask import Flask
from core import init_core, core_cli


app: Flask = Flask(__name__, instance_relative_config=True)
app.config.from_pyfile('config.py')
init_core(app)


if __name__ == '__main__':
    print("Starting flask server...")
    app.run(threaded=True)
else:
    core_cli()

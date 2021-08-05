import requests
import json
import sys
from flask import Flask, request
# from multiprocessing import Process
import webbrowser
import pickle
from datetime import datetime
from decouple import config

SUCCESS_COLOR = "\033[92m"
ERROR_COLOR = "\033[91m"
END_COLOR = "\033[0m"
TIME_FORMAT = "%y-%m-%d"


class MissingConfigError(Exception):
    """Exception raised for missing config field.

    Attributes:
        message
    """

    def __init__(self, message=""):
        self.message = message
        super().__init__(self.message)


# noinspection PyBroadException
class Connection:
    """ This class connects to Ludopedia's API."""

    # noinspection PyBroadException
    def __init__(self, conf_file=config('APP_CONF_PATH')) -> None:
        self.config_required_attrs = ['APP_ID', 'APP_KEY', 'ACCESS_TOKEN', "CODE_URL"]
        self.load_conf(conf_file)
        try:
            self.load_token()
            if (datetime.now() - self.token_reg_date).days >= 60:
                raise Exception
            print(f"{SUCCESS_COLOR}Success!{END_COLOR} token info successfully loaded.")
        except:
            error = f"{ERROR_COLOR}Error:{END_COLOR} Token not existing or expired. Please run connect method"
            print(error, file=sys.stderr)

    def load_conf(self, conf_file=config('APP_CONF_PATH')):
        try:
            # obtém parâmetros a partir de json
            with open(conf_file) as conf:
                conf_dict = json.load(conf)
                for k, v in conf_dict.items():
                    setattr(self, k, v)
            # valida os parâmetros na API
            self.validate_config()
        except Exception as e:
            error = f"{ERROR_COLOR}Error:{END_COLOR} Could not load config file on path {conf_file}."
            error = f"{error}\nDouble check the path and make sure it´s a json file."
            error = f"{error}\n{e}"
            print(error, file=sys.stderr)
            return
        print(f"{SUCCESS_COLOR}Success!{END_COLOR} {conf_file} successfully loaded {self}")

    def connect(self):
        self.validate_config()
        url = f"https://ludopedia.com.br/oauth?app_id={self.APP_ID}&&redirect_uri={self.CODE_URL}"
        print("--------------------------------------------")
        print(f"Please go to this url in your web browser {url}")
        print("--------------------------------------------")
        webbrowser.open(url, new=2)
        app = Flask(__name__)

        @app.route("/")
        def hello_world():
            self.code = request.args['code']
            return self.authenticate(self.code)
            # return "Please go back to your application"

        app.run()

    def authenticate(self, code):
        url = "https://ludopedia.com.br/tokenrequest"
        response = requests.post(url, data={"code": code})
        self.access_token = json.loads(response.text)["access_token"]
        self.save_token(self.access_token)

    def load_token(self):
        with open('data.pickle', 'rb') as f:
            access_info = pickle.load(f)
            self.access_token = access_info['token']
            self.token_reg_date = datetime.strptime(access_info['token_reg_date'], TIME_FORMAT)
            return self.access_token, self.token_reg_date

    def save_token(self, access_token):
        with open('data.pickle', 'wb') as f:
            pickle.dump({"token": access_token, "token_reg_date": datetime.now().strftime(TIME_FORMAT)}, f,
                        pickle.HIGHEST_PROTOCOL)

    def validate_config(self):
        errors = []
        attrs = self.config_required_attrs
        for attr in attrs:
            if not hasattr(self, attr):
                errors.append(
                    f"Configuration {attr} is missing, please add it to your config file and reload the config.")
        if len(errors) > 0:
            raise MissingConfigError("\n".join(errors))

    def __str__(self) -> str:
        conf = "\n".join(map(lambda x: f"{x}: {getattr(self, x)}", self.config_required_attrs))
        return f"config file for Ludopedia API:\n {conf}"


if __name__ == '__main__':
    conn = Connection()
    conn.connect()

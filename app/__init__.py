from flask import Flask

webapp = Flask(__name__)

from app import register
from app import log_in
from app import change_psw

from app import main
from app import upload
from app import pytorch_infer
from app.pytorch_infer import runDetection
from app import hist_list
from app import send_email

UPLOAD_FOLDER = 'app/static/uploads/'
webapp.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

SOLUTION_FOLDER = 'app/static/solutions/'
webapp.config['SOLUTION_FOLDER'] = SOLUTION_FOLDER
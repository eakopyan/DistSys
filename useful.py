from flask import *

app = Flask(__name__)
app.secret_key = 'iswuygdedgv{&75619892__01;;>..zzqwQIHQIWS' #key used to sigh the cookies (unrecommanded...)



if __name__ == '__main__':
  app.run(debug=True)

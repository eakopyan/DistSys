from flask import *

app = Flask(__name__)
app.secret_key = 'iswuygdedgv{&75619892__01;;>..zzqwQIHQIWS' #key used to sigh the cookies (unrecommanded...)

#define routes
@app.route('/')
def index():
  logged = 'logged' in session #'in' verifies wether the dictionnary has any entry
  if logged:
    txt = 'Bonjour %s !' % session['name'] #displays username
  else:
    txt = 'Bonjour illustre inconnu !'
  return render_template('index2.html', message=txt, logged=logged) #calls the index template

@app.route('/login', methods=['POST'])
def login():
  session['name'] = escape(request.form['name']) #'escape' is an additionnal security
  session['logged'] = True
return redirect('/')

if __name__ == '__main__':
  app.run(debug=True)

from flask import Flask,render_template,request,session,redirect,flash
import pymysql
import hashlib
import PyPDF2
import openai
import unicodedata
import os


app = Flask(__name__)
app.secret_key = 'data_transmition'
app.jinja_env.globals.update(len=len)

def sql_connector():
    conn=pymysql.connect(host='localhost',user="root",password='',database='qna_generator')
    cur=conn.cursor()
    return conn,cur

@app.route('/upload', methods=['POST','GET'])
def upload():
    if session['check']==1:
        if request.method == 'POST':
            file = request.files['pdf-file']
            print(file)
            if file.filename!='':
                extracted_text = extract_pdf_data(file)
                session['text']=extracted_text

                from question_PDF import ques_list,answer_list
                n=1
                if n==1:
                    n=n+1
                    # print(ques_list)
                    result=[]
                    for i in range(len(ques_list)):
                        qna="<tr><td>{})</td> <td>{}</td> <td>{}</td></tr>".format((i+1),ques_list[i],answer_list[i].upper())
                        # result.append(render_template_string(qna))
                        result.append(qna)
                    table = "<table border='1' class='table table-striped'><th style='text-align:center;'>SR.NO</<th><th style='text-align:center;'>QUESTIONS</<th><th style='text-align:center;'>Answer</<th>"+"".join(result) + "</table>"
                return render_template("upload.html", ques_data=table)
            else:
                flash('Upload PDF First','error')
                return redirect('/upload')
    else:
        flash('Please Login Again','warning')
        return redirect('/login')
    return render_template("upload.html")

@app.route('/home')
def home():
    if session['check']==1:
        return render_template('home.html')
    else:
        flash("Please Login Again","warning")
    return redirect('/login')

def extract_pdf_data(file):
    reader = PyPDF2.PdfReader(file)
    # Get the number of pages in the PDF
    num_pages = len(reader.pages)
    
    # Initialize an empty string to store the extracted text
    text = ""
    # Loop through all pages and extract the text
    for page in range(num_pages):
        page_obj = reader.pages[page]
        text += page_obj.extract_text()
    # Return the extracted text
    return text

@app.route('/logout',methods=['GET','POST'])
def logout():
    if session['user'] or session['check']==1:
        if request.method == 'POST':
            session.pop("user",None)
            session['check']=0
            return redirect('/login')
    else:
        return redirect('/login')
    return render_template('home.html')

@app.route("/Registration",methods=['GET','POST'])
def register():
    payment_status=request.args.get('payment')
    print(payment_status)
    if payment_status=='1':
        return render_template('Registration.html',payment_status=payment_status)
    if request.method=='POST':
        payment_status=request.form.get('payment_status')
        if payment_status=='1':
            name=request.form.get('u_name')
            email=request.form.get('u_email')
            contact=request.form.get('u_contact')
            password=request.form.get('u_pass')
            enc_pass=hashlib.md5(password.encode()).hexdigest()
            conn,c=sql_connector()
            c.execute("select contact,payment_status from user")
            out=c.fetchall()
            for i in out:
                if i[0]==contact and i[1] == '0':
                    flash('Contact already user.Try different Contact number.', 'error')
                    return redirect('/Registration')
                elif i[0]==contact and i[1] == '1':
                    flash('Contact already user.Try different Contact number.', 'error')
                    return redirect('/Registration?payment=1')
                else:
                    if name!='' or email!='' or contact!='' or password!='':
                        conn,c=sql_connector()
                        c.execute("INSERT INTO user(name,email,contact,password,payment_status) VALUES('{}','{}',{},'{}',{})".format(name,email,int(contact),enc_pass,int(1)))
                        conn.commit()
                        conn.close()
                        flash("Registered Successfull.", "success")
                        return redirect('/login')
                    else: 
                        flash("Please fill the required fields", "error")
        else:
            flash("Please Make Payment first",'error')
    else:
        return render_template('Registration.html')
    return render_template('Registration.html')

@app.route("/login",methods=['GET','POST'])
def login():
    if request.method=='POST':
        uname=request.form.get('u_name')
        upass=request.form.get('u_pass')
        enc_pass=hashlib.md5(upass.encode()).hexdigest()
        conn,c=sql_connector()
        c.execute("select contact,password,payment_status from user")
        out=c.fetchall()
        for i in out:
            if i[0]==uname and i[1]==enc_pass and i[2]==1:
                session['user']=uname
                session['check']=1
                return redirect('/home')
            else:
                flash('Wrong Username or Password', 'error')
    return render_template("login.html")

@app.route("/question",methods=['GET','POST'])
def question():
    if session['check']==1:
        if request.method=='POST':
            if request.form.get('text_data')!='':
                session['t_data'] = request.form.get('text_data')
                from question import ques_list,answer_list
                n=1
                if n==1:
                    n=n+1
                    # print(ques_list)
                    result=[]
                    for i in range(len(ques_list)):
                        qna="<tr><td>{})</td> <td>{}</td> <td>{}</td></tr>".format((i+1),ques_list[i],answer_list[i].upper())
                        # result.append(render_template_string(qna))
                        result.append(qna)
                    table = "<table border='1' class='table table-striped'><th style='text-align:center;'>SR.NO</<th><th style='text-align:center;'>QUESTIONS</<th><th style='text-align:center;'>Answer</<th>"+"".join(result) + "</table>"
                return render_template("MCQ.html", ques_data=table)
            else: 
                flash("Insert Text First","error")
                return redirect('/question')
        else:
            pass
    else:
        flash("Please Login Again","warning")
        return redirect('/login')
    return render_template("MCQ.html")


openai.api_key = "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"
def generate_questions_and_answers(paragraph):
    model_engine = "text-davinci-002"  # choose a language model to use

    # Generate questions using GPT-3
    questions_prompt = f"Generate questions based on the following paragraph:\n\n{paragraph}\n\nQuestions:"
    questions = openai.Completion.create(
        engine=model_engine,
        prompt=questions_prompt,
        max_tokens=1024,
        n=3,
        stop=None,
        temperature=0.5,
    )
    unique_questions = set([q.text.strip() for q in questions.choices])
    # Generate answers to the questions using GPT-3
    answers = []
    for question in unique_questions:
        answer_prompt = f"Answer the following question based on the paragraph and just write the answer not question again:\n\nQuestion: {question}\n\nAnswer:"
        answer = openai.Completion.create(
            engine=model_engine,
            prompt=answer_prompt,
            max_tokens=1024,
            n=3,
            stop=None,
            temperature=0.5,
        )
        answers.append(answer.choices[0].text.strip())

    return {"questions": list(unique_questions), "answers": answers}
@app.route("/theory_text", methods=["POST",'GET'])
def generate_questions():
    if session['check']==1:
        if request.method == 'POST':
            paragraph = request.form["paragraph"]
            if paragraph!='':
                result = generate_questions_and_answers(paragraph)
                questions = result['questions'][0].split('\n')[:-1]
                answers = result['answers'][0].split('\n')[:-1]

                table_rows = ""
                for i in range(len(questions)):
                    table_rows += f"<tr><td>{questions[i]}</td><td>{answers[i]}</td></tr>"

                html_table = f"<table border='1' class='table table-striped'><thead><tr><th>Question</th><th>Answer</th></tr></thead><tbody>{table_rows}</tbody></table>"
                return render_template("theory_text.html", questions=html_table)
            else:
                flash("Insert Text First","error")
                return redirect('/theory_text')
    else:
        flash("Please Login Again","warning")
        return redirect('/login')
    return render_template('theory_text.html')

@app.route("/theory_PDF", methods=["POST",'GET'])
def theory_PDF():
    if session['check']==1:
        if request.method == 'POST':
            file = request.files['pdf-file']
            if file.filename!='':
                max_length=14500
                extracted_text = extract_pdf_data(file)
                extracted_text=extracted_text.replace('\n','')
                normalized_text = unicodedata.normalize('NFKD', extracted_text).encode('ASCII', 'ignore').decode('utf-8')
                shortened_text = normalized_text[:max_length] + '...' if len(normalized_text) > max_length else normalized_text
                print(shortened_text)
                result = generate_questions_and_answers(shortened_text)
                for i in range(len(result['questions'])):
                    questions = result['questions'][i].split('\n')[:-1]
                    answers = result['answers'][i].split('\n')[:-1]

                table_rows = ""
                for i in range(len(questions)):
                    table_rows += f"<tr><td>{questions[i]}</td><td>{answers[i]}</td></tr>"

                html_table = f"<table border='1' class='table table-striped'><thead><tr><th>Question</th><th>Answer</th></tr></thead><tbody>{table_rows}</tbody></table>"
                return render_template("theory_PDF.html", questions=html_table)
            else:
                flash('Upload PDF First','error')
                return redirect('/theory_PDF')
    else:
        flash("Please Login Again","warning")
        return redirect('/login')
    return render_template('theory_PDF.html')


app.run(debug=True)

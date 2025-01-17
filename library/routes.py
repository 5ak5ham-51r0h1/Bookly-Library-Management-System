from flask import render_template,url_for,redirect,flash,request
from library import app,db,bcrypt
from library.forms import RegistrationForm,LoginForm,AddSectionForm,AddBookForm,EditBookForm,RemoveForm
from library.models import User,Section,Book,Request,Feedback
from sqlalchemy import desc,func
from werkzeug.utils import secure_filename
from flask import send_file
import os
import io
import base64
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from flask_login import login_user, current_user, logout_user,login_required
from datetime import datetime,timedelta

@app.route("/")
@app.route("/home")
def home():   
    if current_user.is_authenticated and current_user.user_type=='user':
        return redirect(url_for('loggedin'))
    if current_user.is_authenticated and current_user.user_type=='librarian':
        return redirect(url_for('manage'))
    return render_template('home.html')

@app.route("/login",methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('loggedin'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user)
            if user.user_type=='user':
                next_page = request.args.get('next')
                return redirect(next_page) if next_page else redirect(url_for('loggedin'))
            elif user.user_type=='librarian':
                next_page = request.args.get('next')
                return redirect(next_page) if next_page else redirect(url_for('manage'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', title='Login', form=form)

@app.route("/register",methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('loggedin'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data.lower(), password=hashed_password,user_type="user")
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)
    
@app.route('/statistics')
@login_required
def statistics():
    pending_permits = User.query.filter_by(author_request=True).all()
    user_requests = Request.query.filter_by(UserID=current_user.id).all()
    sections = Section.query.all()
    section_names = [section.SectionName for section in sections]
    issue_counts = []
    for section in sections:
        books = Book.query.filter_by(SectionID=section.SectionID).all()
        issue_count = sum(len(book.requests) for book in books)
        issue_counts.append(issue_count)

    fig, ax = plt.subplots(figsize=(8, 6))
    ax.bar(section_names, issue_counts)
    ax.set_title("Issues per Section showing Popularity", fontweight='bold', fontsize=16)
    ax.set_xlabel("Section")
    ax.set_ylabel("Number of Issues")

    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    graph_url = base64.b64encode(img.getvalue()).decode()
    for request in user_requests:
        if request.book.BookThumbnail:
            request.book.thumbnail_base64 = base64.b64encode(request.book.BookThumbnail).decode('utf-8')

    return render_template('statistics.html', title='Statistics', pending_permits=pending_permits, user_requests=user_requests,graph_url=graph_url)

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route("/membershipupgrade")
@login_required
def upgrade_membership():
    user = User.query.get(current_user.id)
    if user.user_tier == 'standard':
        user.user_tier = 'premium'
        db.session.commit()
        flash('Your membership has been upgraded to Premium.', 'success')
        return redirect(url_for('statistics'))
    else:
        flash('Your membership is already Premium.', 'warning')
        return redirect(url_for('statistics'))

@app.route("/membershipdegrade")
@login_required
def degrade_membership():
    user = User.query.get(current_user.id)
    if user.user_tier == 'premium':
        user.user_tier = 'standard'
        db.session.commit()
        flash('Your membership has been degraded to Standard.', 'success')
        return redirect(url_for('statistics'))
    else:
        flash('Your membership is already standard.', 'warning')
        return redirect(url_for('statistics'))
    
@app.route("/authorrequest")
@login_required
def author_request():
    user = User.query.get(current_user.id)
    if user.author_request == False:
        user.author_request = True
        db.session.commit()
        flash('Applied for author permit successfully!', 'success')
        return redirect(url_for('statistics'))
    elif user.author_request == True:
        flash('Already applied for author permit!', 'warning')
        return redirect(url_for('statistics'))
    
@app.route("/authorrequesthandle/<int:user_id>")
@login_required
def author_approval(user_id):
    user = User.query.get(user_id)
    if user.author_request == True:
        user.author_approval = True
        user.author_request = False
        db.session.commit()
        flash('Author permit approved successfully!', 'success')
        return redirect(url_for('statistics'))
    else:
        return redirect(url_for('statistics'))
    

@app.route("/authorregecthandle/<int:user_id>")
@login_required
def author_regect(user_id):
    user = User.query.get(user_id)
    if user.author_request == True:
        user.author_request = False
        db.session.commit()
        flash('Author permit rejected successfully!', 'warning')
        return redirect(url_for('statistics'))
    else:
        return redirect(url_for('statistics'))
                    
@app.route("/user")
@login_required
def loggedin():
    recent_books = Book.query.order_by(desc(Book.DateCreated)).limit(15).all()
    sections = Section.query.all()
    bestsellers = db.session.query(Book, func.count(Request.RequestID).label('issue_count')).join(Request, Request.BookID == Book.BookID, isouter=True).group_by(Book.BookID).order_by(desc('issue_count')).limit(15).all()
    for book, issue_count in bestsellers:
        if book.BookThumbnail:
            book.thumbnail_base64 = base64.b64encode(book.BookThumbnail).decode('utf-8')
        book.issue_count = issue_count
    for book in recent_books:
        if book.BookThumbnail:
            book.thumbnail_base64 = base64.b64encode(book.BookThumbnail).decode('utf-8')
    if current_user.is_authenticated and current_user.user_type=='user':
        return render_template('loggedin.html', title='Library',sections=sections,recent_books=recent_books,bestsellers=bestsellers)
    else:
        return redirect(url_for('home'))
    
@app.route('/search', methods=['GET'])
@login_required
def search():
    query = request.args.get('query', '').strip()
    if query:
        books = Book.query.filter(
            db.or_(
                Book.BookName.ilike(f'%{query}%'),
                Book.Authors.ilike(f'%{query}%'),
                Section.SectionName.ilike(f'%{query}%')
            )
        ).join(Section).all()

        for book in books:
            if book.BookThumbnail:
                book.thumbnail_base64 = base64.b64encode(book.BookThumbnail).decode('utf-8')

        return render_template('search.html', title='Search', books=books, query=query)

@app.route('/section/<int:section_id>')
@login_required
def section_books(section_id):
    section = Section.query.get(section_id)
    books = Book.query.filter_by(SectionID=section_id).all()
    for book in books:
        if book.BookThumbnail:
            book.thumbnail_base64 = base64.b64encode(book.BookThumbnail).decode('utf-8')
    return render_template('section_books.html',title='Section', section=section, books=books)

@app.route('/book/<int:book_id>')
@login_required
def book_details(book_id):
    book = Book.query.get(book_id)
    section = Section.query.get(book.SectionID)
    section_name = section.SectionName
    book.thumbnail_base64 = base64.b64encode(book.BookThumbnail).decode('utf-8')
    request = Request.query.filter_by(UserID=current_user.id, BookID=book_id).order_by(Request.RequestID.desc()).first()
    is_issued = request.Status == 'Approved' if request else False
    is_bought = request.book_bought if request else False
    recent_feedbacks = Feedback.query.filter_by(BookID=book_id).order_by(Feedback.FeedbackDate.desc()).join(User).all()

    return render_template('book_details.html', title='Book', book=book, is_issued=is_issued, is_bought=is_bought, section_name=section_name,request=request,recent_feedbacks=recent_feedbacks)


@app.route('/download/<int:book_id>')
@login_required
def download_book(book_id):
    book = Book.query.get(book_id)
    return send_file(
            io.BytesIO(book.BookContent),
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f"{book.BookName}.pdf"
        )

@app.route('/buy/<int:book_id>')
@login_required
def buy_book(book_id):
    book = Book.query.get(book_id)
    existing_request = Request.query.filter_by(UserID=current_user.id, BookID=book.BookID, book_bought=True).first()

    # Check if the user has already bought the book
    if existing_request:
        flash('You have already purchased this book.', 'success')
        return redirect(url_for('book_details', book_id=book_id))
    else:
        # Check if a request with the same UserID and BookID exists, but with book_bought=False
        pending_request = Request.query.filter_by(UserID=current_user.id, BookID=book.BookID, book_bought=False).first()

        if pending_request:
            # Update the existing request and mark it as bought
            pending_request.book_bought = True
            db.session.commit()
            flash('Buying request has been successfully processed', 'success')
        else:
            # Create a new request and mark it as bought
            request = Request(
                UserID=current_user.id,
                BookID=book.BookID,
                book_bought=True
            )
            db.session.add(request)
            db.session.commit()
            flash('Buying request has been successfully processed', 'success')
    return redirect(url_for('book_details', book_id=book_id))

@app.route('/read/<int:book_id>')
@login_required
def read_book(book_id):
    book = Book.query.get(book_id)
    return send_file(
            io.BytesIO(book.BookContent),
            mimetype='application/pdf',
            as_attachment=False,
            download_name=f"{book.BookName}.pdf"
        )

@app.route('/issue/<int:book_id>')
@login_required
def issue_book(book_id):
    book = Book.query.get(book_id)
    existing_request = Request.query.filter_by(UserID=current_user.id, BookID=book.BookID, Status='Pending').first()
    if existing_request:
            flash('You have already requested this book. Please wait for the request to be processed.', 'warning')
            return redirect(url_for('book_details', book_id=book_id))
    
    if current_user.user_tier == 'standard':
        pending_requests = Request.query.filter_by(UserID=current_user.id).count()
        if pending_requests >= 5:
            flash('Issue Limit Exhausted! Please return a book before requesting a new one.', 'warning')
            return redirect(url_for('book_details', book_id=book_id))
        
    request = Request(
            UserID=current_user.id,
            BookID=book.BookID,
            Status='Pending'
        )
    db.session.add(request)
    db.session.commit()
    flash('Book issue request has been submitted and is awaiting approval by librarian', 'success')
    return redirect(url_for('book_details', book_id=book_id))

@app.route('/approve_issues')
@login_required
def approve_issues():
    if current_user.user_type == 'librarian':
        pending_requests = Request.query.filter_by(Status='Pending',book_bought=False).all()
        return render_template('approve_issues.html',title='Approve Issue', pending_requests=pending_requests)
    else:
        return redirect(url_for('home'))

@app.route('/revoke_issues')
@login_required
def revoke_issues():
    if current_user.user_type == 'librarian':
        requests = Request.query.filter_by(Status='Approved',book_bought=False).all()
        return render_template('revoke_issues.html',title='Revoke Issue', requests=requests)
    else:
        return redirect(url_for('home'))

@app.route('/approve_request/<int:request_id>')
@login_required
def approve_request(request_id):
    if current_user.user_type == 'librarian':
        request = Request.query.get(request_id)
        if request:
            # Set the issue date and return date
            request.RequestDate = datetime.utcnow()
            request.ReturnDate = request.RequestDate + timedelta(days=7)
            request.Status = 'Approved'
            db.session.commit()

            # Check if the return date has been reached and delete the request
            if request.book_bought==False:
                if datetime.utcnow() >= request.ReturnDate:
                    db.session.delete(request)
                    db.session.commit()
                    flash('Book has been returned.', 'success')
                else:
                    flash('Book request approved.', 'success')
        else:
            flash('Request not found.', 'danger')
        return redirect(url_for('approve_issues'))
    else:
        return redirect(url_for('home'))
    
@app.route('/submit_feedback/<int:book_id>', methods=['POST'])
@login_required
def submit_feedback(book_id):
    feedback_text = request.form.get('feedback')

    if feedback_text and book_id:
        book = Book.query.get(book_id)
        if book:
            # Check if the user has already submitted feedback for this book
            existing_feedback = Feedback.query.filter_by(UserID=current_user.id, BookID=book_id).first()

            if existing_feedback:
                # Update the existing feedback with the new text and date
                existing_feedback.FeedbackText = feedback_text
                existing_feedback.FeedbackDate = datetime.utcnow()
                db.session.commit()
                flash('Your feedback has been updated!', 'success')
            else:
                # Create a new feedback entry
                new_feedback = Feedback(
                    UserID=current_user.id,
                    BookID=book_id,
                    FeedbackText=feedback_text,
                    FeedbackDate=datetime.utcnow()
                )
                db.session.add(new_feedback)
                db.session.commit()
                flash('Thank you for your feedback!', 'success')
        else:
            flash('Book not found.', 'danger')
    else:
        flash('Please provide feedback and book details.', 'warning')

    return redirect(url_for('book_details', book_id=book_id))

@app.route('/reject_request/<int:request_id>')
@login_required
def reject_request(request_id):
    if current_user.is_authenticated:
        request = Request.query.get(request_id)
        if request.book_bought==False:
            db.session.delete(request)
            db.session.commit()
            flash('Book has been successfully returned.', 'success')
        else:
            flash('Request not found.', 'danger')
        return redirect(url_for('revoke_issues'))
    else:
        return redirect(url_for('home'))
                
@app.route("/manage")
def manage():
    if current_user.is_authenticated and current_user.user_type=='librarian':
        return render_template('manage.html', title='Manage')
    else:
        return redirect(url_for('home'))
    
@app.route("/author")
@login_required
def author_view():
    if current_user.author_approval==True and current_user.user_type=='user':
        return render_template('author view.html', title='Author View')
    else:
        return redirect(url_for('home'))


@app.route("/addsection")
def addsection():
    form=AddSectionForm()
    if current_user.is_authenticated and current_user.user_type=='librarian':
        return render_template('addsection.html', title='Add Section',form=form)
    else:
        return redirect(url_for('home'))

@app.route("/addbook")
def addbook():
    form = AddBookForm()
    sections = Section.query.all()
    form.section.choices = [(section.SectionName, section.SectionName) for section in sections]
    if current_user.is_authenticated and current_user.user_type=='librarian':
        return render_template('addbook.html', title='Add Book',form=form)
    else:
        return redirect(url_for('home'))
    
@app.route("/editbook")
def editbook():
    form = EditBookForm()
    if current_user.is_authenticated and current_user.user_type=='librarian':
        return render_template('edit.html', title='Edit Book',form=form)
    else:
        return redirect(url_for('home'))
    
#CRUD API for Sections,Books

@app.route('/api/sections', methods=['POST'])
@login_required
def api_addsection():
    if current_user.is_authenticated and current_user.user_type == 'librarian':
        if request.method == 'POST':
            #fetching form details
            name = request.form['name']
            description = request.form['description']
            existing_section = Section.query.filter_by(SectionName=name).first()
            if existing_section:
                flash('The requested section already exists!', 'warning')
                return redirect(url_for('addsection'))
            
            #adding section
            section = Section(SectionName=name, SectionDescription=description)
            db.session.add(section)
            db.session.commit()
            flash('Requested section has been created!', 'success')
            return redirect(url_for('manage'))
    else:
        return redirect(url_for('home'))


@app.route('/api/addbook', methods=['POST'])
@login_required
def api_addbook():
    if current_user.is_authenticated and current_user.user_type == 'librarian':
        if request.method == 'POST':
            #form details
            name = request.form['book_name']
            authors = request.form['authors']
            section_name = request.form['section']
            book_content = request.files['book_content']
            book_thumbnail = request.files['book_thumbnail']
            book_price = request.form['book_price']
            
            #fetching section details
            section = Section.query.filter_by(SectionName=section_name).first()
            
            #file handling
            book_content_filename = secure_filename(book_content.filename)
            book_thumbnail_filename = secure_filename(book_thumbnail.filename)
            book_content_path = os.path.join(app.config['UPLOAD_FOLDER'], book_content_filename)
            book_thumbnail_path = os.path.join(app.config['UPLOAD_FOLDER'], book_thumbnail_filename)
            book_content.save(book_content_path)
            book_thumbnail.save(book_thumbnail_path)
            with open(book_content_path, 'rb') as file:
                book_content_bytes = file.read()
            with open(book_thumbnail_path, 'rb') as file:
                book_thumbnail_bytes = file.read()
            
            #existing book check
            existing_book = Book.query.filter_by(BookName=name).first()
            if existing_book:
                flash('The requested book already exists!', 'warning')
                return redirect(url_for('addbook'))
            
            #commiting to the db
            new_book = Book(BookName=name, Authors=authors, SectionID=section.SectionID, BookContent=book_content_bytes, BookThumbnail=book_thumbnail_bytes,book_price=book_price)
            db.session.add(new_book)
            db.session.commit()
            flash('Requested book has been created!', 'success')
            return redirect(url_for('manage'))


@app.route('/api/editbook', methods=['POST'])
@login_required
def api_editbook():
    if current_user.is_authenticated and current_user.user_type == 'librarian':
        if request.method == 'POST':
            # Fetching book id from the request
            book_id = request.form.get('book_select')

            if book_id:
                book = Book.query.get(int(book_id))
                if book:
                    # Update the book details
                    book_name = request.form.get('book_name')
                    if book_name:
                        book.BookName = book_name

                    authors = request.form.get('authors')
                    if authors:
                        book.Authors = authors

                    book_price = request.form.get('book_price')
                    if book_price:
                        book.book_price = book_price

                    section_id = request.form.get('section')
                    if section_id:
                        section = Section.query.get(int(section_id))
                        book.SectionID = section.SectionID

                    book_content = request.files.get('book_content')
                    if book_content:
                        book_content_filename = secure_filename(book_content.filename)
                        book_content_path = os.path.join(app.config['UPLOAD_FOLDER'], book_content_filename)
                        book_content.save(book_content_path)
                        with open(book_content_path, 'rb') as file:
                            book.BookContent = file.read()

                    book_thumbnail = request.files.get('book_thumbnail')
                    if book_thumbnail:
                        book_thumbnail_filename = secure_filename(book_thumbnail.filename)
                        book_thumbnail_path = os.path.join(app.config['UPLOAD_FOLDER'], book_thumbnail_filename)
                        book_thumbnail.save(book_thumbnail_path)
                        with open(book_thumbnail_path, 'rb') as file:
                            book.BookThumbnail = file.read()

                    db.session.commit()
                    flash('Book updated successfully.','success')
                    return redirect(url_for('editbook'))
                else:
                    flash('Book not found','danger')
                    return redirect(url_for('editbook'))
            else:
                flash('Book not selected','warning')
            return redirect(url_for('editbook'))
    else:
        return redirect(url_for('home'))

@app.route("/remove")
def remove():
    form = RemoveForm()
    if current_user.is_authenticated and current_user.user_type=='librarian':
        return render_template('remove.html', title='Remove', form=form)
    else:
        return redirect(url_for('home'))

@app.route('/api/delete', methods=['POST'])
@login_required
def api_delete():
    if request.method == 'POST':
        # Fetching book and section from the request
        book_id = request.form.get('book_select')
        section_id = request.form.get('section')

        # Check if the section has any associated books
        section = Section.query.filter_by(SectionID=section_id).first()
        if section:
            if book_id:
                # If the book_select field is filled, proceed to delete the book
                book = Book.query.filter_by(BookID=book_id).first()
                if book:
                    db.session.delete(book)
                    db.session.commit()
                    flash('Book deleted successfully.', 'success')
                    return redirect(url_for('remove'))
                else:
                    flash('Book not found.', 'danger')
                    return redirect(url_for('remove'))
            else:
                # If the book_select field is not filled, proceed with section deletion
                books = Book.query.filter_by(SectionID=section.SectionID).all()
                if books:
                    # If the section has books, do not allow deletion of the section
                    flash('Please remove the books first.', 'warning')
                    return redirect(url_for('remove'))
                else:
                    # If the section has no books, delete the section
                    db.session.delete(section)
                    db.session.commit()
                    flash('Section deleted successfully.', 'success')
                    return redirect(url_for('remove'))
        else:
            flash('Section not provided.', 'danger')
            return redirect(url_for('remove'))

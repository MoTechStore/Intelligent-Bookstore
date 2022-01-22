from unicodedata import category
from django.shortcuts import redirect, render
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.views import generic
#from bootstrap_modal_forms.mixins import PassRequestMixin
from .models import User, Book, Chat, DeleteRequest, Feedback
from django.contrib import messages
from django.db.models import Sum
from django.views.generic import CreateView, DetailView, DeleteView, UpdateView, ListView
from .forms import ChatForm, BookForm, UserForm
from . import models
import operator
import itertools
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth import authenticate, logout
from django.contrib import auth, messages
from django.contrib.auth.hashers import make_password
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.utils import timezone
import random
from django.core.files.storage import FileSystemStorage

# Import Machine learning Packages
import PyPDF2
import pickle
import warnings
warnings.filterwarnings('ignore')
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfTransformer
from sklearn.svm import LinearSVC
from rake_nltk import Rake
rake_nltk_var = Rake()

# Loading Vectorizer from Disk
loaded_vectorizer = pickle.load(open('model/vectorizer.pickle', 'rb'))

# Loading Model from Disk
loaded_model = pickle.load(open('model/classification.model', 'rb'))



@login_required
def uabook(request):
	if request.method == 'POST':
		title = request.POST['title']
		desc = request.POST['desc']
		cover = request.FILES['cover']
		file = request.FILES['pdf']
		current_user = request.user
		user_id = current_user.id
		username = current_user.username

		# Save file to the disk
		fss = FileSystemStorage()
		filename = fss.save(file.name, file)
		url = fss.url(filename)
		print(file.name)
		
		#my_book = ['Machine Learning', 'Django', 'Python', 'Artificial Intelligence', 'Web Development', 'Mobile Apps', 'Programming']
		#category = random.choice(my_book)

		a = Book(title=title, desc=desc, cover=cover, pdf=file, category='', user_id=user_id)
		a.save()

		uploaded_book = Book.objects.filter(title=title, user_id=user_id).values_list('pdf', flat=True)
		u_book = list(uploaded_book)
		u_book = u_book[0]
		print(u_book)

		pdf_path = 'C:/Users/MoTech/Desktop/bookapp/media/' + u_book

		# Open PDF file
		object = PyPDF2.PdfFileReader(pdf_path)
		# Get number of pages
		NumPages = object.getNumPages()
		print('Number of pages are ',NumPages)
		Text = ''
		
		if(NumPages<100):
			print('PDF Book Must Contain At least 100 Pages In Order To Upload In Rep')
			messages.error(request, 'PDF Book Must Contain At least 100 Pages In Order To Upload')
			return redirect('publisher')
		else:
			print('This PDF Qualifies, Waiting To Be Uploaded')
			# Extracting Text of 20 First pages
			for i in range(0,40):
				PageObj = object.getPage(i)
				Text += PageObj.extractText()
			print(Text)
			
			# Making prediction using Model and vectorizer loaded from Disk
			prediction = loaded_model.predict(loaded_vectorizer.transform([Text])[0])
			print(prediction[0])
			prediction = prediction[0]
			
			Book.objects.filter(pdf = u_book).update(category = prediction, status=True)
			messages.success(request, 'Book was uploaded successfully')
			return redirect('publisher')
	else:
	    messages.error(request, 'Book was not uploaded successfully')
	    return redirect('uabook_form')



# Shared Views
def login_form(request):
	return render(request, 'bookstore/login.html')


def logoutView(request):
	logout(request)
	return redirect('home')


def loginView(request):
	if request.method == 'POST':
		username = request.POST['username']
		password = request.POST['password']
		user = authenticate(request, username=username, password=password)
		if user is not None and user.is_active:
			auth.login(request, user)
			if user.is_admin or user.is_superuser:
				return redirect('dashboard')
			elif user.is_librarian:
				return redirect('librarian')
			else:
			    return redirect('publisher')
		else:
		    messages.error(request, "Invalid username or password")
		    return redirect('home')


def register_form(request):
	return render(request, 'bookstore/register.html')


def registerView(request):
	if request.method == 'POST':
		username = request.POST['username']
		email = request.POST['email']
		password = request.POST['password']
		password = make_password(password)

		a = User(username=username, email=email, password=password)
		a.save()
		messages.success(request, 'Account was created successfully')
		return redirect('home')
	else:
	    messages.error(request, 'Registration fail, try again later')
	    return redirect('regform')



















			


# Publisher views
@login_required
def publisher(request):
	return render(request, 'publisher/home.html')


#@login_required
def uabook_form(request):
	return render(request, 'publisher/add_book.html')


@login_required
def request_form(request):
	return render(request, 'publisher/delete_request.html')


@login_required
def feedback_form(request):
	return render(request, 'publisher/send_feedback.html')

@login_required
def about(request):
	return render(request, 'publisher/about.html')	


def usearch(request):
    query = request.GET['query']
    print(type(query))
    print("Word T be searched", query)

    data = query.split()
    print(data)
    '-'.join(data)
    data = ' '.join(data)
    print(data)
    print(len(data))

    text = data
    rake_nltk_var.extract_keywords_from_text(text)
    keyword_extracted = rake_nltk_var.get_ranked_phrases()
    print(keyword_extracted)
    my_keyword = keyword_extracted
    '-'.join(my_keyword)
    print("Extracted Word By ML")
    print(' '.join(my_keyword))
    data = ' '.join(my_keyword)

    print("New Word According to ML", data)
    print(data)
    print("Before Again")

    if( len(data) == 0):
      return redirect('publisher')
    else:
                print("Again")
                print(data)

                count = {}
                results = {}
                results['posts']= Book.objects.none() # empty QuerySet
                queries = data.split()
                print("my query below")
                print(queries)
                for query in queries:
                    results['posts'] = results['posts'] | Book.objects.filter(category__icontains=query, status=True)
                    count['posts'] = results['posts'].count()


                count1 = {}
                queries1 = data.split()
                results1 = {}
                results1['posts']= Book.objects.none() # empty QuerySet
                queries1 = data.split()
                for query1 in queries:
                    results1['posts'] = results1['posts'] | Book.objects.filter(category__startswith=query1, status=True)
                    count1['posts'] = results1['posts'].count()

                count2 = {}
                queries2 = data.split()
                results2 = {}
                results2['posts'] = Book.objects.none()  # empty QuerySet
                queries2 = data.split()
                for query2 in queries:
                    results2['posts'] = results2['posts'] | Book.objects.filter(category__endswith=query2, status=True)
                    count2['posts'] = results2['posts'].count() 


                files = itertools.chain(results['posts'], results1['posts'], results2['posts'])

                res = []
                for i in files:
                    if i not in res:
                        res.append(i)

                # word variable will be shown in html when user click on search button
                word="Searched Result :"

                print(res)
                files = res

                page = request.GET.get('page', 1)
                paginator = Paginator(files, 10)
                try:
                    files = paginator.page(page)
                except PageNotAnInteger:
                    files = paginator.page(1)
                except EmptyPage:
                    files = paginator.page(paginator.num_pages)   

                if files:
                    return render(request,'publisher/result.html',{'files':files,'word':word})
                return render(request,'publisher/result.html',{'files':files,'word':word})



@login_required
def search(request):
    query = request.GET['query']
    print(type(query))


    #data = query.split()
    data = query
    print(len(data))
    if( len(data) == 0):
        return redirect('publisher')
    else:
                a = data

                # Searching for It
                qs5 =models.Book.objects.filter(category__iexact=a).distinct()
                qs6 =models.Book.objects.filter(category__exact=a).distinct()

                qs7 =models.Book.objects.all().filter(category__contains=a)
                qs8 =models.Book.objects.select_related().filter(category__contains=a).distinct()
                qs9 =models.Book.objects.filter(category__startswith=a).distinct()
                qs10 =models.Book.objects.filter(category__endswith=a).distinct()
                qs11 =models.Book.objects.filter(category__istartswith=a).distinct()
                qs12 =models.Book.objects.all().filter(category__icontains=a)
                qs13 =models.Book.objects.filter(category__iendswith=a).distinct()




                files = itertools.chain(qs5, qs6, qs7, qs8, qs9, qs10, qs11, qs12, qs13)

                res = []
                for i in files:
                    if i not in res:
                        res.append(i)


                # word variable will be shown in html when user click on search button
                word="Searched Result :"
                print("Result")

                print(res)
                files = res




                page = request.GET.get('page', 1)
                paginator = Paginator(files, 10)
                try:
                    files = paginator.page(page)
                except PageNotAnInteger:
                    files = paginator.page(1)
                except EmptyPage:
                    files = paginator.page(paginator.num_pages)
   


                if files:
                    return render(request,'publisher/result.html',{'files':files,'word':word})
                return render(request,'publisher/result.html',{'files':files,'word':word})



@login_required
def delete_request(request):
	if request.method == 'POST':
		book_id = request.POST['delete_request']
		current_user = request.user
		user_id = current_user.id
		username = current_user.username
		user_request = username + "  want book with id  " + book_id + " to be deleted"

		a = DeleteRequest(delete_request=user_request)
		a.save()
		messages.success(request, 'Request was sent')
		return redirect('request_form')
	else:
	    messages.error(request, 'Request was not sent')
	    return redirect('request_form')



@login_required
def send_feedback(request):
	if request.method == 'POST':
		feedback = request.POST['feedback']
		current_user = request.user
		user_id = current_user.id
		username = current_user.username
		feedback = username + " " + " says " + feedback

		a = Feedback(feedback=feedback)
		a.save()
		messages.success(request, 'Feedback was sent')
		return redirect('feedback_form')
	else:
	    messages.error(request, 'Feedback was not sent')
	    return redirect('feedback_form')


























class UBookListView(LoginRequiredMixin,ListView):
	model = Book
	template_name = 'publisher/book_list.html'
	context_object_name = 'books'
	#paginate_by = 2

	def get_queryset(self):
		return Book.objects.filter(status=True).order_by('-id')





class UCreateChat(LoginRequiredMixin, CreateView):
	form_class = ChatForm
	model = Chat
	template_name = 'publisher/chat_form.html'
	success_url = reverse_lazy('ulchat')


	def form_valid(self, form):
		self.object = form.save(commit=False)
		self.object.user = self.request.user
		self.object.save()
		return super().form_valid(form)


class UListChat(LoginRequiredMixin, ListView):
	model = Chat
	template_name = 'publisher/chat_list.html'

	def get_queryset(self):
		return Chat.objects.filter(posted_at__lt=timezone.now()).order_by('posted_at')































# Librarian views
def librarian(request):
	book = Book.objects.all().count()
	user = User.objects.all().count()

	context = {'book':book, 'user':user}

	return render(request, 'librarian/home.html', context)


@login_required
def labook_form(request):
	return render(request, 'librarian/add_book.html')


@login_required
def labook(request):
	if request.method == 'POST':
		title = request.POST['title']
		author = request.POST['author']
		year = request.POST['year']
		publisher = request.POST['publisher']
		desc = request.POST['desc']
		cover = request.FILES['cover']
		pdf = request.FILES['pdf']
		current_user = request.user
		user_id = current_user.id
		username = current_user.username

		a = Book(title=title, author=author, year=year, publisher=publisher, 
			desc=desc, cover=cover, pdf=pdf, uploaded_by=username, user_id=user_id)
		a.save()
		messages.success(request, 'Book was uploaded successfully')
		return redirect('llbook')
	else:
	    messages.error(request, 'Book was not uploaded successfully')
	    return redirect('llbook')



class LBookListView(LoginRequiredMixin,ListView):
	model = Book
	template_name = 'librarian/book_list.html'
	context_object_name = 'books'
	paginate_by = 3

	def get_queryset(self):
		return Book.objects.order_by('-id')


class LManageBook(LoginRequiredMixin,ListView):
	model = Book
	template_name = 'librarian/manage_books.html'
	context_object_name = 'books'
	paginate_by = 3

	def get_queryset(self):
		return Book.objects.order_by('-id')


class LDeleteRequest(LoginRequiredMixin,ListView):
	model = DeleteRequest
	template_name = 'librarian/delete_request.html'
	context_object_name = 'feedbacks'
	paginate_by = 3

	def get_queryset(self):
		return DeleteRequest.objects.order_by('-id')


class LViewBook(LoginRequiredMixin,DetailView):
	model = Book
	template_name = 'librarian/book_detail.html'

	
class LEditView(LoginRequiredMixin,UpdateView):
	model = Book
	form_class = BookForm
	template_name = 'librarian/edit_book.html'
	success_url = reverse_lazy('lmbook')
	success_message = 'Data was updated successfully'


class LDeleteView(LoginRequiredMixin,DeleteView):
	model = Book
	template_name = 'librarian/confirm_delete.html'
	success_url = reverse_lazy('lmbook')
	success_message = 'Data was deleted successfully'


class LDeleteBook(LoginRequiredMixin,DeleteView):
	model = Book
	template_name = 'librarian/confirm_delete2.html'
	success_url = reverse_lazy('librarian')
	success_message = 'Data was dele successfully'



@login_required
def lsearch(request):
    query = request.GET['query']
    print(type(query))


    #data = query.split()
    data = query
    print(len(data))
    if( len(data) == 0):
        return redirect('publisher')
    else:
                a = data

                # Searching for It
                qs5 =models.Book.objects.filter(id__iexact=a).distinct()
                qs6 =models.Book.objects.filter(id__exact=a).distinct()

                qs7 =models.Book.objects.all().filter(id__contains=a)
                qs8 =models.Book.objects.select_related().filter(id__contains=a).distinct()
                qs9 =models.Book.objects.filter(id__startswith=a).distinct()
                qs10 =models.Book.objects.filter(id__endswith=a).distinct()
                qs11 =models.Book.objects.filter(id__istartswith=a).distinct()
                qs12 =models.Book.objects.all().filter(id__icontains=a)
                qs13 =models.Book.objects.filter(id__iendswith=a).distinct()




                files = itertools.chain(qs5, qs6, qs7, qs8, qs9, qs10, qs11, qs12, qs13)

                res = []
                for i in files:
                    if i not in res:
                        res.append(i)


                # word variable will be shown in html when user click on search button
                word="Searched Result :"
                print("Result")

                print(res)
                files = res




                page = request.GET.get('page', 1)
                paginator = Paginator(files, 10)
                try:
                    files = paginator.page(page)
                except PageNotAnInteger:
                    files = paginator.page(1)
                except EmptyPage:
                    files = paginator.page(paginator.num_pages)
   


                if files:
                    return render(request,'librarian/result.html',{'files':files,'word':word})
                return render(request,'librarian/result.html',{'files':files,'word':word})


class LCreateChat(LoginRequiredMixin, CreateView):
	form_class = ChatForm
	model = Chat
	template_name = 'librarian/chat_form.html'
	success_url = reverse_lazy('llchat')


	def form_valid(self, form):
		self.object = form.save(commit=False)
		self.object.user = self.request.user
		self.object.save()
		return super().form_valid(form)




class LListChat(LoginRequiredMixin, ListView):
	model = Chat
	template_name = 'librarian/chat_list.html'

	def get_queryset(self):
		return Chat.objects.filter(posted_at__lt=timezone.now()).order_by('posted_at')














# Admin views

def dashboard(request):
	book = Book.objects.all().count()
	user = User.objects.all().count()

	context = {'book':book, 'user':user}

	return render(request, 'dashboard/home.html', context)

def create_user_form(request):
    choice = ['1', '0', 'Publisher', 'Admin', 'Librarian']
    choice = {'choice': choice}

    return render(request, 'dashboard/add_user.html', choice)


class ADeleteUser(SuccessMessageMixin, DeleteView):
    model = User
    template_name='dashboard/confirm_delete3.html'
    success_url = reverse_lazy('aluser')
    success_message = "Data successfully deleted"


class AEditUser(SuccessMessageMixin, UpdateView): 
    model = User
    form_class = UserForm
    template_name = 'dashboard/edit_user.html'
    success_url = reverse_lazy('aluser')
    success_message = "Data successfully updated"

class ListUserView(generic.ListView):
    model = User
    template_name = 'dashboard/list_users.html'
    context_object_name = 'users'
    paginate_by = 4

    def get_queryset(self):
        return User.objects.order_by('-id')

def create_user(request):
    choice = ['1', '0', 'Publisher', 'Admin', 'Librarian']
    choice = {'choice': choice}
    if request.method == 'POST':
            first_name=request.POST['first_name']
            last_name=request.POST['last_name']
            username=request.POST['username']
            userType=request.POST['userType']
            email=request.POST['email']
            password=request.POST['password']
            password = make_password(password)
            print("User Type")
            print(userType)
            if userType == "Publisher":
                a = User(first_name=first_name, last_name=last_name, username=username, email=email, password=password, is_publisher=True)
                a.save()
                messages.success(request, 'Member was created successfully!')
                return redirect('aluser')
            elif userType == "Admin":
                a = User(first_name=first_name, last_name=last_name, username=username, email=email, password=password, is_admin=True)
                a.save()
                messages.success(request, 'Member was created successfully!')
                return redirect('aluser')
            elif userType == "Librarian":
                a = User(first_name=first_name, last_name=last_name, username=username, email=email, password=password, is_librarian=True)
                a.save()
                messages.success(request, 'Member was created successfully!')
                return redirect('aluser')    
            else:
                messages.success(request, 'Member was not created')
                return redirect('create_user_form')
    else:
        return redirect('create_user_form')


class ALViewUser(DetailView):
    model = User
    template_name='dashboard/user_detail.html'



class ACreateChat(LoginRequiredMixin, CreateView):
	form_class = ChatForm
	model = Chat
	template_name = 'dashboard/chat_form.html'
	success_url = reverse_lazy('alchat')


	def form_valid(self, form):
		self.object = form.save(commit=False)
		self.object.user = self.request.user
		self.object.save()
		return super().form_valid(form)




class AListChat(LoginRequiredMixin, ListView):
	model = Chat
	template_name = 'dashboard/chat_list.html'

	def get_queryset(self):
		return Chat.objects.filter(posted_at__lt=timezone.now()).order_by('posted_at')


@login_required
def aabook_form(request):
	return render(request, 'dashboard/add_book.html')


@login_required
def aabook(request):
	if request.method == 'POST':
		title = request.POST['title']
		author = request.POST['author']
		year = request.POST['year']
		publisher = request.POST['publisher']
		desc = request.POST['desc']
		cover = request.FILES['cover']
		pdf = request.FILES['pdf']
		current_user = request.user
		user_id = current_user.id
		username = current_user.username

		a = Book(title=title, author=author, year=year, publisher=publisher, 
			desc=desc, cover=cover, pdf=pdf, uploaded_by=username, user_id=user_id)
		a.save()
		messages.success(request, 'Book was uploaded successfully')
		return redirect('albook')
	else:
	    messages.error(request, 'Book was not uploaded successfully')
	    return redirect('aabook_form')


class ABookListView(LoginRequiredMixin,ListView):
	model = Book
	template_name = 'dashboard/book_list.html'
	context_object_name = 'books'
	paginate_by = 3

	def get_queryset(self):
		return Book.objects.order_by('-id')




class AManageBook(LoginRequiredMixin,ListView):
	model = Book
	template_name = 'dashboard/manage_books.html'
	context_object_name = 'books'
	paginate_by = 3

	def get_queryset(self):
		return Book.objects.order_by('-id')




class ADeleteBook(LoginRequiredMixin,DeleteView):
	model = Book
	template_name = 'dashboard/confirm_delete2.html'
	success_url = reverse_lazy('ambook')
	success_message = 'Data was dele successfully'


class ADeleteBookk(LoginRequiredMixin,DeleteView):
	model = Book
	template_name = 'dashboard/confirm_delete.html'
	success_url = reverse_lazy('dashboard')
	success_message = 'Data was dele successfully'


class AViewBook(LoginRequiredMixin,DetailView):
	model = Book
	template_name = 'dashboard/book_detail.html'




class AEditView(LoginRequiredMixin,UpdateView):
	model = Book
	form_class = BookForm
	template_name = 'dashboard/edit_book.html'
	success_url = reverse_lazy('ambook')
	success_message = 'Data was updated successfully'




class ADeleteRequest(LoginRequiredMixin,ListView):
	model = DeleteRequest
	template_name = 'dashboard/delete_request.html'
	context_object_name = 'feedbacks'
	paginate_by = 3

	def get_queryset(self):
		return DeleteRequest.objects.order_by('-id')



class AFeedback(LoginRequiredMixin,ListView):
	model = Feedback
	template_name = 'dashboard/feedback.html'
	context_object_name = 'feedbacks'
	paginate_by = 3

	def get_queryset(self):
		return Feedback.objects.order_by('-id')



@login_required
def asearch(request):
    query = request.GET['query']
    print(type(query))


    #data = query.split()
    data = query
    print(len(data))
    if( len(data) == 0):
        return redirect('dashborad')
    else:
                a = data

                # Searching for It
                qs5 =models.Book.objects.filter(id__iexact=a).distinct()
                qs6 =models.Book.objects.filter(id__exact=a).distinct()

                qs7 =models.Book.objects.all().filter(id__contains=a)
                qs8 =models.Book.objects.select_related().filter(id__contains=a).distinct()
                qs9 =models.Book.objects.filter(id__startswith=a).distinct()
                qs10 =models.Book.objects.filter(id__endswith=a).distinct()
                qs11 =models.Book.objects.filter(id__istartswith=a).distinct()
                qs12 =models.Book.objects.all().filter(id__icontains=a)
                qs13 =models.Book.objects.filter(id__iendswith=a).distinct()




                files = itertools.chain(qs5, qs6, qs7, qs8, qs9, qs10, qs11, qs12, qs13)

                res = []
                for i in files:
                    if i not in res:
                        res.append(i)


                # word variable will be shown in html when user click on search button
                word="Searched Result :"
                print("Result")

                print(res)
                files = res




                page = request.GET.get('page', 1)
                paginator = Paginator(files, 10)
                try:
                    files = paginator.page(page)
                except PageNotAnInteger:
                    files = paginator.page(1)
                except EmptyPage:
                    files = paginator.page(paginator.num_pages)
   


                if files:
                    return render(request,'dashboard/result.html',{'files':files,'word':word})
                return render(request,'dashboard/result.html',{'files':files,'word':word})

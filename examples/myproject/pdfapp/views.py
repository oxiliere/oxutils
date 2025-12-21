import io
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404
from django.core.files.base import ContentFile
from django.views.generic import ListView, DetailView

from oxutils.pdf import Printer, WeasyTemplateView
from .models import Profile
from .pdf_helpers import get_stylesheets


class ProfileListView(ListView):
    model = Profile
    template_name = 'pdfapp/profile_list.html'
    context_object_name = 'profiles'


class ProfileDetailView(DetailView):
    model = Profile
    template_name = 'pdfapp/profile_detail.html'
    context_object_name = 'profile'


class ProfilePDFView(WeasyTemplateView):
    template_name = 'pdfapp/profile_pdf.html'

    def get_pdf_stylesheets(self):
        return get_stylesheets('css1/pdf_style.css')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile = get_object_or_404(Profile, pk=self.kwargs['pk'])
        context['profile'] = profile
        return context

    def get_pdf_filename(self):
        profile = get_object_or_404(Profile, pk=self.kwargs['pk'])
        return f'cv_{profile.name.replace(" ", "_")}.pdf'


def generate_and_save_cv(request, pk):
    profile = get_object_or_404(Profile, pk=pk)
    
    printer = Printer(
        template_name='pdfapp/profile_pdf.html',
        context={'profile': profile},
        stylesheets=get_stylesheets('css/pdf_style.css'),
    )
    
    obj = io.BytesIO()
    printer.write_pdf(output=obj)
    
    filename = f'cv_{profile.name.replace(" ", "_")}.pdf'
    profile.curriculum_vitae.save(filename, ContentFile(obj.getvalue()), save=True)
    
    return HttpResponse(
        f'CV generated and saved for {profile.name}. '
        f'<a href="/profile/{pk}/">View profile</a>'
    )


def download_standalone_pdf(request, pk):
    profile = get_object_or_404(Profile, pk=pk)
    
    printer = Printer(
        template_name='pdfapp/profile_pdf.html',
        context={'profile': profile},
        stylesheets=get_stylesheets('css/pdf_style.css'),
    )
    
    pdf_bytes = printer.write_pdf()
    
    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="cv_{profile.name.replace(" ", "_")}.pdf"'
    
    return response

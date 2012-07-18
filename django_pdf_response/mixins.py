import os
from xhtml2pdf import pisa
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

from django.template.loader import render_to_string
from django.http import HttpResponse, HttpResponseServerError
from django.core.exceptions import ImproperlyConfigured
from django.conf import settings



def fetch_resources(uri, rel):
    if uri.startswith(settings.STATIC_URL):
        path = os.path.join(settings.STATIC_ROOT, 
            uri.replace(settings.STATIC_URL, ""))
    elif uri.startswith(settings.MEDIA_URL):
        path = os.path.join(settings.MEDIA_ROOT, 
            uri.replace(settings.MEDIA_URL, ""))
    else:
        path = uri
    return path


class PDFResponseMixin(object):
    """
    Normally this should be used with any of django.views.generic views, which 
    inherit from TemplateResponseMixin.
    """
    output_filename = None
    encoding = None

    def get_output_filename(self):
        output_filename = self.output_filename
        if output_filename is None:
            raise ImproperlyConfigured(
                "You should set the 'output_filename' attribute."
                )

        explicit_ext = output_filename.rsplit('.', 1) == 'pdf'
        if not explicit_ext:
            output_filename += '.pdf'
        return output_filename

    def get_encoding(self):
        return self.encoding or getattr(settings, 'PDF_DEFAULT_ENCODING', 
            'utf-8')

    def render_to_response(self, context, **kwargs):
        encoding = self.get_encoding()
        context['encoding'] = encoding.upper()

        buffer = StringIO()
        html = render_to_string(self.get_template_names()[0], context)
        pdf = pisa.CreatePDF(StringIO(html.encode(encoding)), buffer, 
            show_error_as_pdf=True, encoding=encoding, 
            link_callback=fetch_resources)
        if pdf.err:
            response = HttpResponseServerError(
                    'Got %s errors trying to convert to pdf.' % pdf.err
                )
        else:
            response = HttpResponse(mimetype='application/pdf')
            response['Content-Disposition'] = \
                'attachment; filename=%s' % self.get_output_filename()
            response.write(buffer.getvalue())
        buffer.close()

        return response

import urllib.parse

from django.db import transaction
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import get_template
from django.template import Template
from django.urls import reverse
from django.views.decorators.clickjacking import xframe_options_exempt
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.csrf import csrf_exempt

from ..base.models import User
from ..files.models import File
from ..settings import EVAL_FRAME_ORIGIN, MAX_FILE_SIZE, MAX_FILENAME_LENGTH, SITE_URL
from ..views import get_base_page_info_dict, get_user_info_dict
from .models import Notebook, NotebookRevision
from .names import get_random_compound


def _get_user_info_json(user):
    if user.is_authenticated:
        return get_user_info_dict(user)
    return {}


@xframe_options_exempt
def eval_frame_view(request):
    return render(request, "notebook_eval_frame.html", {"editor_origin": SITE_URL})


def _get_iframe_src():
    return urllib.parse.urljoin(EVAL_FRAME_ORIGIN, reverse(eval_frame_view))


@ensure_csrf_cookie
def notebook_view(request, pk):
    notebook = get_object_or_404(Notebook, pk=pk)
    if "revision" in request.GET:
        try:
            revision_id = int(request.GET["revision"])
        except ValueError:
            return HttpResponseBadRequest(content=f'Invalid revision id: {request.GET["revision"]}')
        revision = get_object_or_404(NotebookRevision, notebook=notebook, pk=revision_id)
        latest_revision_id = notebook.revisions.latest("created").id
    else:
        revision = notebook.revisions.first()
        latest_revision_id = revision.id

    notebook_info = {
        "username": notebook.owner.username,
        "user_can_save": notebook.owner_id == request.user.id,
        "notebook_id": notebook.id,
        "revision_id": revision.id,
        "revision_is_latest": revision.id == latest_revision_id,
        "connectionMode": "SERVER",
        "title": revision.title,
        "max_filename_length": MAX_FILENAME_LENGTH,
        "max_file_size": MAX_FILE_SIZE,
    }
    if notebook.forked_from is not None:
        notebook_info["forked_from"] = notebook.forked_from.id
    else:
        notebook_info["forked_from"] = False
    return render(
        request,
        "notebook.html",
        {
            "title": revision.title,
            "user_info": _get_user_info_json(request.user),
            "notebook_info": notebook_info,
            "iomd": revision.content,
            "iframe_src": _get_iframe_src(),
            "eval_frame_origin": EVAL_FRAME_ORIGIN,
        },
    )


@ensure_csrf_cookie
def notebook_revisions(request, pk):
    pk = int(pk)
    nb = get_object_or_404(Notebook, pk=pk)
    owner = get_object_or_404(User, pk=nb.owner_id)
    owner_info = {
        "username": owner.username,
        "full_name": owner.get_full_name(),
        "avatar": owner.avatar,
        "title": nb.title,
        "notebookId": nb.id,
    }
    if nb.forked_from is not None:
        owner_info["forkedFromTitle"] = nb.forked_from.title
        owner_info["forkedFromRevisionID"] = nb.forked_from.id
        owner_info["forkedFromNotebookID"] = nb.forked_from.notebook_id
        owner_info["forkedFromUsername"] = nb.forked_from.notebook.owner.username

    files = [
        {
            "filename": file.filename,
            "id": file.id,
            "last_updated": file.last_updated.isoformat(),
            "size": len(file.content),
        }
        for file in File.objects.filter(notebook_id=pk).order_by("-last_updated")
    ]
    revisions = list(
        [
            {
                "id": revision.id,
                "notebookId": revision.notebook_id,
                "title": revision.title,
                "date": revision.created.isoformat(),
            }
            for revision in NotebookRevision.objects.filter(notebook_id=pk)
        ]
    )
    return render(
        request,
        "../templates/index.html",
        {
            "title": f"Revisions - {nb.title}",
            "page_data": {
                **get_base_page_info_dict(),
                "userInfo": get_user_info_dict(request.user),
                "ownerInfo": owner_info,
                "revisions": revisions,
                "files": files,
            },
        },
    )


def _get_new_notebook_content(iomd):
    if iomd:
        return iomd
    # default is to create a new notebook from our default template
    print(get_template("new_notebook_content.iomd").backend)
    return get_template("new_notebook_content.iomd").render()


def _get_iomd_params(iomd):
    if iomd:
        return f"?iomd={urllib.parse.quote_plus(iomd)}"
    return ""


@ensure_csrf_cookie
def new_notebook_view(request):
    iomd = request.GET.get("iomd")
    if not request.user.is_authenticated:
        return redirect(reverse("try-it") + _get_iomd_params(iomd))

    # create a new notebook and redirect to its view
    with transaction.atomic():
        notebook = Notebook.objects.create(owner=request.user)
        NotebookRevision.objects.create(
            notebook=notebook,
            content=_get_new_notebook_content(iomd),
            title=get_random_compound(),
            is_draft=True,
        )
    return redirect(notebook)


@ensure_csrf_cookie
def tryit_view(request):
    """
    A way to let new users experiment with iodide without logging in

    If user is logged in, redirect to `/new/`
    """
    iomd = request.GET.get("iomd")
    if request.user.is_authenticated:
        return redirect(reverse(new_notebook_view) + _get_iomd_params(iomd))

    print(_get_new_notebook_content(iomd))
    return render(
        request,
        "notebook.html",
        {
            "user_info": {},
            "notebook_info": {
                "connectionMode": "SERVER",
                "tryItMode": True,
                "title": "Untitled notebook",
            },
            "iomd": _get_new_notebook_content(iomd),
            "iframe_src": _get_iframe_src(),
            "eval_frame_origin": EVAL_FRAME_ORIGIN,
        },
    )

'''
    Let user use his own template file and data
    template and data should be enclosed in a POST request.
'''
@csrf_exempt
def customize_view(request):

    if request.method == "POST":
        
        postedTemplate = request.FILES['template']
        postedData = request.FILES['data']
    
        template = postedTemplate.read().decode()
        data = postedData.read().decode()

        iomd = template + data

        return render(
        request,
        "notebook.html",
        {
            "user_info": {},
            "notebook_info": {
                "connectionMode": "SERVER",
                "tryItMode": True,
                "title": "POST SUCCESS",
            },
            "iomd": _get_new_notebook_content(iomd),
            "iframe_src": _get_iframe_src(),
            "eval_frame_origin": EVAL_FRAME_ORIGIN,
        },
    )
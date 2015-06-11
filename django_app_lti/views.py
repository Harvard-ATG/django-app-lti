from django.http import HttpResponse
from django.shortcuts import redirect
from django.core.urlresolvers import reverse
from django.contrib.auth import logout
from django.views.generic import View
from django.conf import settings

from ims_lti_py.tool_config import ToolConfig
from braces.views import CsrfExemptMixin, LoginRequiredMixin

from .models import LTIResource, LTICourse, LTICourseUser

LTI_SETUP = settings.LTI_SETUP

def logout_view(request):
    logout(request)
    return redirect("lti:logged-out")

def logged_out_view(request):
    return HttpResponse('Logged out successfully.')

class LTILaunchView(CsrfExemptMixin, LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        '''Shows an error message because LTI launch requests must be POSTed.'''
        content = 'Invalid LTI launch request.'
        return HttpResponse(content, content_type='text/html', status=200)

    def post(self, request, *args, **kwargs):
        '''Handles the LTI launch request and redirects to the main page. '''
        
        # Collect a subset of the LTI launch parameters for mapping the
        # tool resource instance to this app's internal course instance.
        launch = {
            "consumer_key": request.POST.get('oauth_consumer_key', None),
            "resource_link_id": request.POST.get('resource_link_id', None),
            "context_id": request.POST.get('context_id', None),
            "course_name_short": request.POST.get("context_label"),
            "course_name": request.POST.get("context_title"),
            "canvas_course_id": request.POST.get('custom_canvas_course_id', None),
        }
        
        # Lookup tool resource, uniquely identified by the combination of:
        #
        #  * oauth consumer key
        #  * resource link ID
        #
        # These are required attributes specified by LTI (context ID is not).
        # If no LTI resource is found, automatically setup a new course instance
        # and associate it with the LTI resource.
        resource_identifiers = [launch[x] for x in ('consumer_key', 'resource_link_id')]
        if LTIResource.hasCourse(*resource_identifiers):
            lti_resource = LTIResource.getResource(*resource_identifiers)
        else:
            lti_resource = LTIResource.setupCourse(launch)
        
        # Associate the authenticated user with the course instance.
        launch_roles = request.POST.get('roles', '')
        if LTICourseUser.hasCourseUser(user=request.user, course=lti_resource.course):
            lti_course_user = LTICourseUser.getCourseUser(user=request.user, course=lti_resource.course)
            lti_course_user.updateRoles(launch_roles)
        else:
            lti_course_user = LTICourseUser.createCourseUser(user=request.user, course=lti_resource.course, roles=launch_roles)
        
        # Save the course ID in the session
        course_id = lti_resource.course.id
        request.session['course_id'] = lti_resource.course.id
        
        # Redirect back to the index
        return redirect(reverse(LTI_SETUP['LAUNCH_REDIRECT_URL'], kwargs={"course_id": course_id}))

class LTIToolConfigView(View):
    LAUNCH_URL = LTI_SETUP.get('LTI_LAUNCH_URL', 'lti:launch')
    """
    Outputs LTI configuration XML for Canvas as specified in the IMS Global Common Cartridge Profile.

    The XML produced by this view can either be copy-pasted into the Canvas tool
    settings, or exposed as an endpoint to Canvas by linking to this view.
    """
    def get_launch_url(self, request):
        '''
        Returns the launch URL for the LTI tool. When a secure request is made,
        a secure launch URL will be supplied.
        '''
        if request.is_secure():
            host = 'https://' + request.get_host()
        else:
            host = 'http://' + request.get_host()
        return host + reverse(self.LAUNCH_URL);

    def set_ext_params(self, lti_tool_config):
        '''
        Sets extension parameters on the ToolConfig() instance.
        This includes vendor-specific things like the course_navigation
        and privacy level.

        EXAMPLE_EXT_PARAMS = {
            "canvas.instructure.com": {
                "privacy_level": "public",
                "course_navigation": {
                    "enabled": "true",
                    "default": "disabled",
                    "text": "MY tool (localhost)",
                }
            }
        }
        '''
        EXT_PARAMS = LTI_SETUP.get("EXTENSION_PARAMETERS", {})
        for ext_key in EXT_PARAMS:
            for ext_param in EXT_PARAMS[ext_key]:
                ext_value = EXT_PARAMS[ext_key][ext_param]
                lti_tool_config.set_ext_param(ext_key, ext_param, ext_value)

    def get_tool_config(self, request):
        '''
        Returns an instance of ToolConfig().
        '''
        launch_url = self.get_launch_url(request)
        return ToolConfig(
            title=LTI_SETUP['TOOL_TITLE'],
            description=LTI_SETUP['TOOL_DESCRIPTION'],
            launch_url=launch_url,
            secure_launch_url=launch_url,
        )

    def get(self, request, *args, **kwargs):
        '''
        Returns the LTI tool configuration as XML.
        '''
        lti_tool_config = self.get_tool_config(request)
        self.set_ext_params(lti_tool_config)
        return HttpResponse(lti_tool_config.to_xml(), content_type='text/xml', status=200)


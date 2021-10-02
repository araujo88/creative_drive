from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from .serializers import UploadSerializer
from file_upload.models import Upload

@api_view(['GET'])
def getRoutes(request):

    routes = [
        {'GET':'/api/uploads'},
        {'GET':'/api/uploads/id'},
        {'POST':'/api/uploads/upload'},

        {'POST':'/api/users/token'},
        {'POST':'/api/users/token/refresh'},

    ]

    return Response(routes)

@api_view(['GET'])
def getUploads(request):
#    print('USER:', request.user)
    uploads = Upload.objects.all()
    serializer = UploadSerializer(uploads, many = True)
    return Response(serializer.data)

@api_view(['GET'])
def getUpload(request, pk):
    upload = Upload.objects.get(id=pk)
    serializer = UploadSerializer(upload, many = False)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def makeUpload(request):
    data = request.data
    current_user = request.user
    file = data['upload']
    #file_name = data['name']
    #file = Upload.objects.create(upload=file, user=current_user, name=file_name)
    file = Upload.objects.create(upload=file)
    serializer = UploadSerializer(file, many = False)
    return Response(serializer.data)

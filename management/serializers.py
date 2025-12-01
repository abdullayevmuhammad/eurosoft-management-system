from rest_framework import serializers
from .models import Project, Sprint, Task
from accounts.models import User

class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = [
            'id',
            'title',
            'start_date',
            'end_date',
            'status',
            'pm',
            'created_at',
            'updated_at',
        ]


class SprintSerializer(serializers.ModelSerializer):
    task_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Sprint
        fields = [
            'id',
            'project',
            'name',
            'start_date',
            'duration_days',
            'status',
            'task_count',
            'created_at',
            'updated_at',
        ]



class TaskSerializer(serializers.ModelSerializer):
    assignees = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=User.objects.all()
    )

    class Meta:
        model = Task
        fields = [
            'id',
            'sprint',
            'title',
            'description',
            'assignees',  
            'start_date',
            'due_date',
            'status',
            'created_at',
            'updated_at',
        ]

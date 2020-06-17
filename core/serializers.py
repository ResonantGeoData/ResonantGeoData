from rest_framework import serializers

from .models import Algorithm, Task, Dataset

from . import models


class AlgorithmSerializer(serializers.ModelSerializer):
    class Meta:
        model = Algorithm
        fields = '__all__'


class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = '__all__'

class DatasetSerializer(serializers.ModelSerializer):
	class Meta:
		model = Dataset
		fields = '__all__'

class GroundtruthSerializer(serializers.ModelSerializer):
	class Meta:
		model = models.Groundtruth
		fields = '__all__'

class ScoreAlgorithmSerializer(serializers.ModelSerializer):
	class Meta:
		model = models.ScoreAlgorithm
		fields = '__all__'

class AlgorithmJobSerializer(serializers.ModelSerializer):
	class Meta:
		model = models.AlgorithmJob
		fields = '__all__'

class AlgorithmResultSerializer(serializers.ModelSerializer):
	class Meta:
		model = models.AlgorithmResult
		fields = '__all__'

class ScoreJobSerializer(serializers.ModelSerializer):
	class Meta:
		model = models.ScoreJob
		fields = '__all__'

class ScoreResultSerializer(serializers.ModelSerializer):
	class Meta:
		model = models.ScoreResult
		fields = '__all__'
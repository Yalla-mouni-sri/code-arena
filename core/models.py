from django.db import models
from accounts.models import Admin, Coder

class Question(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    created_by = models.ForeignKey(Admin, on_delete=models.CASCADE, related_name='questions_posted')
    created_at = models.DateTimeField(auto_now_add=True)
    is_closed = models.BooleanField(default=False) # Added as per instruction
    
    class Meta:
        db_table = 'question'

    def __str__(self):
        return self.title

class Solution(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='solutions')
    coder = models.ForeignKey(Coder, on_delete=models.CASCADE, related_name='solutions')
    code = models.TextField()
    language = models.CharField(max_length=50)
    points_left = models.IntegerField(default=3)
    flag = models.BooleanField(default=True)
    evaluation = models.CharField(max_length=50, blank=True, null=True)
    submitted_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'solution'
        unique_together = ('question', 'coder')

    def __str__(self):
        return f"{self.coder.rollno} - {self.question.title}"

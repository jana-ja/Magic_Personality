"""
Django-Admin für den Fragebogen und die Testergebnisse (D-71).

Fragen und Antworten sind hier nur lesbar: eine veröffentlichte Version
ist unveränderlich (FR-T6) und kommt ausschließlich über
`seed_questionnaire` in die Datenbank (D-28). Änderbar bleibt an
`Questionnaire` selbst nur, was auch nach der Veröffentlichung
änderbar sein soll — insbesondere der Schwellenwert `T` (R-4).
Testergebnisse sind Nutzerdaten und ebenfalls nur lesbar (löschen
bleibt möglich).
"""

from django.contrib import admin

from .models import AnswerOption, Question, Questionnaire, TestResult


class ReadOnlyAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(Questionnaire)
class QuestionnaireAdmin(admin.ModelAdmin):
    list_display = ["version", "question_count", "published_at", "result_threshold"]


@admin.register(Question)
class QuestionAdmin(ReadOnlyAdmin):
    list_display = ["questionnaire", "position", "dimension", "text"]
    list_filter = ["questionnaire", "dimension"]

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(AnswerOption)
class AnswerOptionAdmin(ReadOnlyAdmin):
    list_display = ["question", "position", "color", "text"]
    list_filter = ["question__questionnaire", "color"]

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(TestResult)
class TestResultAdmin(ReadOnlyAdmin):
    list_display = ["profile", "questionnaire_version", "result_colors", "scores", "taken_at"]
    list_filter = ["questionnaire_version"]
    search_fields = ["profile__nickname"]

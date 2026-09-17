# Von Hand nachbearbeitet: `accounts.ColorAssignment.test_result` und
# `quiz.TestResult.profile` verweisen wechselseitig aufeinander
# (accounts <-> quiz). Das automatisch erzeugte Migrations-Paar bildete
# dadurch einen echten Zyklus (accounts.0002 <-> quiz.0001) und ließ
# sich nicht mehr anwenden. Aufgelöst durch Aufteilen: `ColorAssignment`
# entsteht in 0002 zunächst ohne `test_result`, dieses Feld kommt erst
# hier hinzu, nachdem `quiz.0001_initial` (und damit die Tabelle für
# `quiz.TestResult`) bereits existiert.

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_profile_colorassignment_and_more'),
        ('quiz', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='colorassignment',
            name='test_result',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='color_assignments', to='quiz.testresult'),
        ),
    ]

# Generated manually — increases action max_length for named actions.

from django.db import migrations, models
import django.contrib.postgres.fields


class Migration(migrations.Migration):

    dependencies = [
        ("permissions", "0009_grant_is_active"),
    ]

    operations = [
        migrations.AlterField(
            model_name="grant",
            name="actions",
            field=django.contrib.postgres.fields.ArrayField(
                base_field=models.CharField(max_length=50),
                size=None,
            ),
        ),
        migrations.AlterField(
            model_name="rolegrant",
            name="actions",
            field=django.contrib.postgres.fields.ArrayField(
                base_field=models.CharField(max_length=50),
                size=None,
            ),
        ),
    ]

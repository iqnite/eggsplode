from tortoise import migrations
from tortoise.migrations import operations as ops
import functools
from json import dumps, loads
from tortoise.fields.base import OnDelete
from tortoise import fields

class Migration(migrations.Migration):
    dependencies = [('models', '0001_initial')]

    initial = False

    operations = [
        ops.CreateModel(
            name='Recipe',
            fields=[
                ('id', fields.CharField(primary_key=True, unique=True, db_index=True, max_length=128)),
                ('json_data', fields.JSONField(encoder=functools.partial(dumps, separators=(',', ':')), decoder=loads)),
            ],
            options={'table': 'recipe', 'app': 'models', 'pk_attr': 'id'},
            bases=['Model'],
        ),
        ops.CreateModel(
            name='UserRecipe',
            fields=[
                ('id', fields.IntField(generated=True, primary_key=True, unique=True, db_index=True)),
                ('user', fields.ForeignKeyField('models.User', source_field='user_id', db_constraint=True, to_field='user_id', related_name='recipes', on_delete=OnDelete.CASCADE)),
                ('recipe', fields.ForeignKeyField('models.Recipe', source_field='recipe_id', db_constraint=True, to_field='id', on_delete=OnDelete.CASCADE)),
            ],
            options={'table': 'userrecipe', 'app': 'models', 'unique_together': (('user', 'recipe'),), 'pk_attr': 'id'},
            bases=['Model'],
        ),
    ]

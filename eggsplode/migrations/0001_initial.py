from tortoise import migrations
from tortoise.migrations import operations as ops
from tortoise.fields.base import OnDelete
from tortoise import fields

class Migration(migrations.Migration):
    initial = True

    operations = [
        ops.CreateModel(
            name='Card',
            fields=[
                ('code_name', fields.CharField(primary_key=True, unique=True, db_index=True, max_length=64)),
            ],
            options={'table': 'card', 'app': 'models', 'pk_attr': 'code_name'},
            bases=['Model'],
        ),
        ops.CreateModel(
            name='User',
            fields=[
                ('user_id', fields.BigIntField(generated=True, primary_key=True, unique=True, db_index=True)),
                ('is_profile_public', fields.BooleanField(default=True)),
                ('color', fields.IntField(default=16685060)),
                ('games_played', fields.IntField(default=0)),
                ('games_won', fields.IntField(default=0)),
                ('has_cheated', fields.BooleanField(default=False)),
                ('custom_recipes_created', fields.IntField(default=0)),
                ('most_nopes_in_a_row', fields.IntField(default=0)),
                ('has_won_classic_without_defuse', fields.BooleanField(default=False)),
                ('has_won_classic_without_cards', fields.BooleanField(default=False)),
                ('most_cards_won_classic', fields.IntField(default=0)),
                ('warnings_ignored', fields.IntField(default=0)),
                ('respects_paid', fields.IntField(default=0)),
                ('times_scammed', fields.IntField(default=0)),
                ('largest_player_count_won', fields.IntField(default=0)),
            ],
            options={'table': 'user', 'app': 'models', 'pk_attr': 'user_id'},
            bases=['Model'],
        ),
        ops.CreateModel(
            name='UserCardUsage',
            fields=[
                ('id', fields.IntField(generated=True, primary_key=True, unique=True, db_index=True)),
                ('user', fields.ForeignKeyField('models.User', source_field='user_id', db_constraint=True, to_field='user_id', related_name='card_usages', on_delete=OnDelete.CASCADE)),
                ('card', fields.ForeignKeyField('models.Card', source_field='card_id', db_constraint=True, to_field='code_name', on_delete=OnDelete.CASCADE)),
                ('use_count', fields.IntField(default=0)),
            ],
            options={'table': 'usercardusage', 'app': 'models', 'unique_together': (('user', 'card'),), 'pk_attr': 'id'},
            bases=['Model'],
        ),
    ]

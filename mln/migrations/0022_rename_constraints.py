# Generated by Django 2.2 on 2020-01-07 19:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mln', '0021_mlnmessagebody'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='messagebodycategory',
            options={'verbose_name_plural': 'Message body categories'},
        ),
        migrations.RemoveConstraint(
            model_name='arcadeprize',
            name='unique_module_item_item',
        ),
        migrations.RemoveConstraint(
            model_name='attachment',
            name='unique_message_item',
        ),
        migrations.RemoveConstraint(
            model_name='blueprintrequirement',
            name='unique_blueprint_item_item',
        ),
        migrations.RemoveConstraint(
            model_name='inventorystack',
            name='unique_owner_item',
        ),
        migrations.RemoveConstraint(
            model_name='iteminfo',
            name='unique_name_type',
        ),
        migrations.RemoveConstraint(
            model_name='module',
            name='unique_owner_pos',
        ),
        migrations.RemoveConstraint(
            model_name='moduleexecutioncost',
            name='unique_module_item_item',
        ),
        migrations.RemoveConstraint(
            model_name='modulesetupcost',
            name='unique_module_item_item',
        ),
        migrations.RemoveConstraint(
            model_name='networkermessageattachment',
            name='unique_trigger_item',
        ),
        migrations.AddConstraint(
            model_name='arcadeprize',
            constraint=models.UniqueConstraint(fields=('module_item', 'item'), name='arcade_prize_unique_module_item_item'),
        ),
        migrations.AddConstraint(
            model_name='attachment',
            constraint=models.UniqueConstraint(fields=('message', 'item'), name='attachment_unique_message_item'),
        ),
        migrations.AddConstraint(
            model_name='blueprintrequirement',
            constraint=models.UniqueConstraint(fields=('blueprint_item', 'item'), name='blueprint_requirement_unique_blueprint_item_item'),
        ),
        migrations.AddConstraint(
            model_name='inventorystack',
            constraint=models.UniqueConstraint(fields=('owner', 'item'), name='inventory_stack_unique_owner_item'),
        ),
        migrations.AddConstraint(
            model_name='iteminfo',
            constraint=models.UniqueConstraint(fields=('name', 'type'), name='item_info_unique_name_type'),
        ),
        migrations.AddConstraint(
            model_name='module',
            constraint=models.UniqueConstraint(fields=('owner', 'pos_x', 'pos_y'), name='module_unique_owner_pos'),
        ),
        migrations.AddConstraint(
            model_name='moduleexecutioncost',
            constraint=models.UniqueConstraint(fields=('module_item', 'item'), name='module_execution_cost_unique_module_item_item'),
        ),
        migrations.AddConstraint(
            model_name='modulesetupcost',
            constraint=models.UniqueConstraint(fields=('module_item', 'item'), name='module_setup_cost_unique_module_item_item'),
        ),
        migrations.AddConstraint(
            model_name='networkermessageattachment',
            constraint=models.UniqueConstraint(fields=('trigger', 'item'), name='networker_message_attachment_unique_trigger_item'),
        ),
    ]
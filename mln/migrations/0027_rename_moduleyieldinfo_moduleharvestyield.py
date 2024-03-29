# Generated by Django 3.2.7 on 2021-10-21 05:42

from django.db import migrations
from django.db import models
import mln.models.static

class Migration(migrations.Migration):
	dependencies = [
		('mln', '0026_messagebody_type'),
	]

	operations = [
		# Rename ModuleYieldInfo --> ModuleHarvestYield
		migrations.RenameModel(
			old_name='ModuleYieldInfo',
			new_name='ModuleHarvestYield',
		),

		# Add some related_name's and item constraints
		migrations.AlterField(
			model_name='moduleharvestyield',
			name='item',
			field=models.OneToOneField(limit_choices_to=models.Q(('type', mln.models.static.ItemType['MODULE'])), on_delete=models.deletion.CASCADE, related_name='+', to='mln.iteminfo'),
		),
		migrations.AlterField(
			model_name='moduleexecutioncost',
			name='module_item',
			field=models.ForeignKey(limit_choices_to=models.Q(('type', mln.models.static.ItemType['MODULE'])), on_delete=models.deletion.CASCADE, related_name='execution_costs', to='mln.iteminfo'),
		),
		migrations.AlterField(
			model_name='modulesetupcost',
			name='module_item',
			field=models.ForeignKey(limit_choices_to=models.Q(('type', mln.models.static.ItemType['MODULE'])), on_delete=models.deletion.CASCADE, related_name='setup_costs', to='mln.iteminfo'),
		),

		# Create ModuleOwnerYield
		migrations.CreateModel(
			name='ModuleOwnerYield',
			fields=[
				('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
				('qty', models.PositiveSmallIntegerField()),
				('item', models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='+', to='mln.iteminfo')),
				('module_item', models.ForeignKey(limit_choices_to=models.Q(('type', mln.models.static.ItemType['MODULE'])), on_delete=models.deletion.CASCADE, related_name='owner_yields', to='mln.iteminfo')),
				('probability', models.PositiveSmallIntegerField()),
			],
		),
		migrations.AddConstraint(
			model_name='moduleowneryield',
			constraint=models.UniqueConstraint(fields=('module_item', 'item'), name='module_owner_yield_unique_module_item_item'),
		),

		# ArcadePrize --> ModuleGuestYield
		migrations.RenameModel(
			old_name="ArcadePrize",
			new_name="ModuleGuestYield",
		),
		migrations.RemoveConstraint(
			model_name='moduleguestyield',
			name='arcade_prize_unique_module_item_item',
		),
		migrations.AddConstraint(
			model_name='moduleguestyield',
			constraint=models.UniqueConstraint(fields=('module_item', 'item'), name='module_guest_yield_unique_module_item_item'),
		),
		migrations.AlterField(
			model_name='moduleguestyield',
			name='module_item',
			field=models.ForeignKey(limit_choices_to=models.Q(('type', mln.models.static.ItemType['MODULE'])), on_delete=models.deletion.CASCADE, related_name='guest_yields', to='mln.iteminfo'),
		),
		migrations.RenameField(
			model_name='moduleguestyield',
			old_name='success_rate',
			new_name='probability',
		),

		# Create ModuleMessage
		migrations.CreateModel(
			name='ModuleMessage',
			fields=[
				('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
				('probability', models.PositiveSmallIntegerField()),
				('message', models.OneToOneField(on_delete=models.deletion.CASCADE, related_name='+', to='mln.messagetemplate')),
				('module_item', models.ForeignKey(limit_choices_to=models.Q(('type', mln.models.static.ItemType['MODULE'])), on_delete=models.deletion.CASCADE, related_name='friend_messages', to='mln.iteminfo')),
			],
		),

		migrations.AddConstraint(
		  model_name='modulemessage',
		  constraint=models.UniqueConstraint(fields=('module_item',), name='module_message_unique_module_item'),
		),
	]

# Generated by Django 3.2.7 on 2021-10-21 05:42

from django.db import migrations
from django.db import models

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

		# Add some related_name's 
		migrations.AlterField(
			model_name='moduleexecutioncost',
			name='module_item',
			field=models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='execution_costs', to='mln.iteminfo'),
		),
		migrations.AlterField(
			model_name='modulesetupcost',
			name='module_item',
			field=models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='setup_costs', to='mln.iteminfo'),
		),

		# Create ModuleOwnerYield and ModuleGuestYield
		migrations.CreateModel(
			name='ModuleOwnerYield',
			fields=[
				('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
				('qty', models.PositiveSmallIntegerField()),
				('item', models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='+', to='mln.iteminfo')),
				('module_item', models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='owner_yields', to='mln.iteminfo')),
			],
		),
		migrations.CreateModel(
			name='ModuleGuestYield',
			fields=[
				('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
				('qty', models.PositiveSmallIntegerField()),
				('item', models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='+', to='mln.iteminfo')),
				('module_item', models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='guest_yields', to='mln.iteminfo')),
			],
		),
		migrations.AddConstraint(
			model_name='moduleowneryield',
			constraint=models.UniqueConstraint(fields=('module_item', 'item'), name='module_owner_yield_unique_module_item_item'),
		),
		migrations.AddConstraint(
			model_name='moduleguestyield',
			constraint=models.UniqueConstraint(fields=('module_item', 'item'), name='module_guest_yield_unique_module_item_item'),
		),
	]
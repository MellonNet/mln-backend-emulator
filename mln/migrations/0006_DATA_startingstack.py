import os.path
import xml.etree.ElementTree as et

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

from mln.models.static import StartingStack

def import_xml(apps, schema_editor):
	xml = et.parse(os.path.abspath(os.path.join(settings.STATICFILES_DIRS[1], "XMLCache/MLN/MLN_1033_20100211081940.xml")))
	for xml_stack in xml.findall("startingStacks/stack"):
		item_id = int(xml_stack.get("itemID"))
		qty = int(xml_stack.get("qty"))
		StartingStack.objects.create(item_id=item_id, qty=qty)

def undo(apps, schema_editor):
	StartingStack.objects.all().delete()

class Migration(migrations.Migration):
	dependencies = [
		('mln', '0005_null_blank'),
	]

	operations = [
		migrations.CreateModel(
			name='StartingStack',
			fields=[
				('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
				('qty', models.PositiveSmallIntegerField()),
				('item', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to='mln.ItemInfo')),
			],
			options={
				'abstract': False,
			},
		),
		migrations.RunPython(import_xml, undo),
	]

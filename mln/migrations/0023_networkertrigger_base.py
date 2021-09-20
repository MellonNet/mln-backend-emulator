# Generated by Django 3.2.7 on 2021-09-20 03:23

from django.db import migrations, models
import django.db.models.deletion

def migrate_message_triggers(apps, schema_editor): 
	# Copies fields from NetworkerMessageTrigger to NetworkerTrigger
	NetworkerMessageTrigger = apps.get_model("mln", "NetworkerMessageTrigger")
	NetworkerTrigger = apps.get_model("mln", "NetworkerTrigger")
	for message_trigger in NetworkerMessageTrigger.objects.all():
		NetworkerTrigger.objects.create(id=message_trigger.id, response=message_trigger.body)
		message_trigger.networkertrigger_ptr_id = message_trigger.id
		message_trigger.save()
		# for attachment in message_trigger.attachments.all():
		# 	attachment.

def temp(*args, **kwargs): print("\nHere")

class Migration(migrations.Migration):
	dependencies = [
		('mln', '0022_rename_constraints'),
	]

	operations = [
		# 1. Create NetworkerTrigger (NT): networker, response
		# 2. Migrate all NetworkerMessageTriggers (NMT)
		# 3. Remove outdated NMT fields (networker, body)
		# 4. Create new NMT fields (message_body, message_attachment)
		# 5. Migrate all NetworkerMessageAttachment.trigger

		# Step 1. Create NMT with required fields
		migrations.CreateModel(
			name='NetworkerTrigger',
			fields=[
				('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
				('networker', models.ForeignKey(to="auth.user", null=True, default=None, related_name="+", on_delete=models.CASCADE, limit_choices_to={"profile__is_networker": True})),
				('response', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to='mln.messagebody')),
			],
		),

		# Step 2. Migrate NMTs to NTs with the same ID
		migrations.AddField(
			model_name='networkermessagetrigger',
			name='networkertrigger_ptr',
			field=models.OneToOneField(auto_created=True, default=None, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='mln.networkertrigger'),
			preserve_default=False,
		),
		migrations.RunPython(temp),
		migrations.RunPython(migrate_message_triggers),

		# Step 3. Remove outdated NMT fields
		migrations.RemoveField(
			model_name='networkermessagetrigger',
			name='body',
		),
		migrations.RemoveField(
			model_name='networkermessagetrigger',
			name='id',
		),
		migrations.RemoveField(
			model_name='networkermessagetrigger',
			name='networker',
		),

		# Step 4. Create new NMT fields
		migrations.AddField(
			model_name='networkermessagetrigger',
			name='message_body',
			field=models.ForeignKey(to="mln.messagebody", related_name="+", on_delete=models.CASCADE, blank=True, null=True),
			preserve_default=False,
		),
		migrations.AddField(
			model_name='networkermessagetrigger',
			name='message_attachment',
			field=models.ForeignKey(to="mln.iteminfo", related_name="+", on_delete=models.CASCADE, blank=True, null=True),
			preserve_default=False,
		),

		# Step 5. Migrate NMA.trigger
		migrations.AlterField(
			model_name='networkermessageattachment',
			name='trigger',
			field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attachments', to='mln.networkertrigger'),
		),
	]

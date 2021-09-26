# Generated by Django 3.2.7 on 2021-09-26 18:40

from django.db import migrations, models
import django.db.models.deletion

def migrate_nrt(apps, schema_editor):
	# # Migrates all NetworkerMessageTrigger to MessageTemplate + NetworkerReply
	NetworkerMessageTrigger = apps.get_model("mln", "NetworkerMessageTriggerLegacy")
	NetworkerMessageAttachment = apps.get_model("mln", "NetworkerMessageAttachmentLegacy")
	MessageTemplate = apps.get_model("mln", "MessageTemplate")
	MessageTemplateAttachment = apps.get_model("mln", "MessageTemplateAttachment")
	NetworkerReply = apps.get_model("mln", "NetworkerReply")

	for legacy_trigger in NetworkerMessageTrigger.objects.all():
		template = MessageTemplate.objects.create(body=legacy_trigger.body)
		for attachment in legacy_trigger.attachments.all():
			new_attachment = template.attachments.create(item=attachment.item, qty=attachment.qty)
			attachment.updated = new_attachment
			attachment.save()
		reply = NetworkerReply.objects.create(template=template)
		legacy_trigger.updated = reply
		legacy_trigger.save()

class Migration(migrations.Migration):

	dependencies = [
		('mln', '0023_message_template'),
	]

	operations = [
		migrations.CreateModel(
			name='NetworkerReply',
			fields=[
				('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
				('message_attachment', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='mln.iteminfo')),
				('message_body', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='mln.messagebody')),
				('template', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to='mln.messagetemplate')),
			],			
      options={'verbose_name_plural': 'Networker replies'},
		),
		migrations.AddField(
		    model_name='networkermessageattachmentlegacy',
		    name='updated',
		    field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='legacy', to='mln.messagetemplateattachment'),
		),
		migrations.AddField(
		    model_name='networkermessagetriggerlegacy',
		    name='updated',
		    field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='legacy', to='mln.networkerreply'),
		),
		migrations.RunPython(migrate_nrt, reverse_code=migrations.RunPython.noop),
	]
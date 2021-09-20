# Generated by Django 3.2.7 on 2021-09-20 03:23

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

def create_NRTs(apps, schema_editor): 
	# Create an NMT for each NT
	NetworkerReplyTrigger = apps.get_model("mln", "NetworkerReplyTrigger")
	MessageTemplate = apps.get_model("mln", "MessageTemplate")
	for template in MessageTemplate.objects.all():
		NetworkerReplyTrigger.objects.create(messagetemplate_ptr=template)

class Migration(migrations.Migration):
	dependencies = [
		('mln', '0022_rename_constraints'),
	]

	operations = [
		# 1. Rename NetworkerReplyTrigger (NRT) to MessageTemplate (MT)
		# 2. Migrate MT fields: networker_name, networker, response, source
		# 3. Create NRT: message_body, message_attachment
		# 4. Create an NRT for every existing MT
		# 5. Rename NetworkerMessageAttachment to MessageTemplateAttachment

		# Step 1. Rename NRT to MT
		migrations.RenameModel(
			old_name="NetworkerMessageTrigger",
			new_name="MessageTemplate",
		),

		# Step 2. Migrate MessageTemplate fields
		migrations.RenameField(  # networker -> networker_name
			model_name="messagetemplate",
			old_name="networker",
			new_name="networker_name",
		),
		migrations.RenameField(  # body --> response
			model_name="messagetemplate",
			old_name="body",
			new_name="response"
		),
		migrations.AddField(  # create networker
			model_name="messagetemplate",
			name="networker",
			field=models.ForeignKey(limit_choices_to={'profile__is_networker': True}, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to=settings.AUTH_USER_MODEL),
		),
		migrations.AlterField(  # make source nullable
			model_name="messagetemplate",
			name="source",
			field=models.TextField(blank=True, null=True),
		),

		# Step 3. Create (new) NetworkerReplyTrigger
		migrations.CreateModel(
			name="NetworkerReplyTrigger",
			fields=[
				("message_body", models.ForeignKey(to="mln.messagebody", related_name="+", on_delete=models.CASCADE, blank=True, null=True)),
				("message_attachment", models.ForeignKey(to="mln.iteminfo", related_name="+", on_delete=models.CASCADE, blank=True, null=True)),
				("messagetemplate_ptr", models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='mln.messagetemplate')),
			]
		),

		# Step 4. Create MessageTemplates
		migrations.RunPython(create_NRTs, reverse_code=migrations.RunPython.noop),

		# Step 5. Rename NetworkerMessageAttachment to MessageTemplateAttachment
		migrations.RenameModel(
			old_name="NetworkerMessageAttachment",
			new_name="MessageTemplateAttachment",
		),
		migrations.RemoveConstraint(
			model_name='messagetemplateattachment',
			name='networker_message_attachment_unique_trigger_item',
		),
		migrations.RenameField(
			model_name="messagetemplateattachment",
			old_name="trigger",
			new_name="template",
		),
		migrations.AddConstraint(
			model_name='messagetemplateattachment',
			constraint=models.UniqueConstraint(fields=('template', 'item'), name='networker_template_attachment_unique_template_item'),
		),
	]

from peewee import (AutoField, BigIntegerField, DateField, FloatField, Model,
                    SqliteDatabase, TextField)

db = SqliteDatabase('db.sqlite3')


class BaseModel(Model):
    class Meta:
        database = db


class Payers(BaseModel):
    id = AutoField(column_name='ID')
    uid = BigIntegerField(column_name='UID')
    name = TextField(column_name='Name', null=True)
    code = TextField(column_name='Code')
    sum = FloatField(column_name='Sum', null=True)
    purpose = TextField(column_name='Purpose', null=True)
    date = DateField(column_name='Date', null=True)

    class Meta:
        table_name = 'Payers'


class Users(BaseModel):
    id = AutoField(column_name='ID')
    name = TextField(column_name='Name')
    id_gram = TextField(column_name='ID Gram')
    role = TextField(column_name='Role', default=0)

    class Meta:
        table_name = 'Users'


if __name__ == '__main__':
    db.create_tables([Payers, Users])

from marshmallow import Schema, fields, validate

class UserSchema(Schema):
    # ...existing code...

class LoanApplicationSchema(Schema):
    """Loan application validation schema."""
    amount = fields.Decimal(required=True, validate=validate.Range(min=0))
    purpose = fields.Str(required=True, validate=validate.Length(min=5, max=500))
    term_months = fields.Integer(required=True, validate=validate.Range(min=1, max=60))
    submit_date = fields.DateTime(required=True)

class DocumentSchema(Schema):
    """Document validation schema."""
    document_type = fields.Str(required=True, validate=validate.OneOf([
        'id_proof', 'income_proof', 'address_proof', 'loan_application'
    ]))
    document_url = fields.Url(required=True)
    file_name = fields.Str(required=True, validate=validate.Length(min=1, max=255))

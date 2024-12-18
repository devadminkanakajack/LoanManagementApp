--
-- PostgreSQL database dump
--

-- Dumped from database version 16.6
-- Dumped by pg_dump version 16.4

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


ALTER TABLE public.alembic_version OWNER TO neondb_owner;

--
-- Name: analytics; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.analytics (
    id integer NOT NULL,
    metric_type text NOT NULL,
    metric_value numeric NOT NULL,
    dimension text NOT NULL,
    dimension_value text NOT NULL,
    created_at timestamp without time zone DEFAULT now()
);


ALTER TABLE public.analytics OWNER TO neondb_owner;

--
-- Name: analytics_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.analytics_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.analytics_id_seq OWNER TO neondb_owner;

--
-- Name: analytics_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.analytics_id_seq OWNED BY public.analytics.id;


--
-- Name: borrower; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.borrower (
    id integer NOT NULL,
    user_id integer NOT NULL,
    phone_number character varying(20) NOT NULL,
    address character varying(200) NOT NULL,
    employment_status character varying(50) NOT NULL,
    monthly_income double precision NOT NULL,
    created_at timestamp without time zone NOT NULL
);


ALTER TABLE public.borrower OWNER TO neondb_owner;

--
-- Name: borrower_details; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.borrower_details (
    id integer NOT NULL,
    user_id integer NOT NULL,
    marital_status character varying(20),
    dependents integer,
    education character varying(50),
    employment_type character varying(50),
    income_source character varying(100),
    monthly_income numeric(10,2),
    other_income numeric(10,2),
    existing_loans boolean DEFAULT false,
    credit_score integer,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    identification_number character varying(50),
    tax_id character varying(50),
    employer_details jsonb,
    bank_details jsonb,
    reference_details jsonb
);


ALTER TABLE public.borrower_details OWNER TO neondb_owner;

--
-- Name: borrower_details_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.borrower_details_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.borrower_details_id_seq OWNER TO neondb_owner;

--
-- Name: borrower_details_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.borrower_details_id_seq OWNED BY public.borrower_details.id;


--
-- Name: borrower_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.borrower_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.borrower_id_seq OWNER TO neondb_owner;

--
-- Name: borrower_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.borrower_id_seq OWNED BY public.borrower.id;


--
-- Name: borrowers; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.borrowers (
    id integer NOT NULL,
    user_id integer,
    phone_number text NOT NULL,
    address text NOT NULL,
    employment_status text NOT NULL,
    monthly_income numeric NOT NULL,
    created_at timestamp without time zone DEFAULT now()
);


ALTER TABLE public.borrowers OWNER TO neondb_owner;

--
-- Name: borrowers_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.borrowers_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.borrowers_id_seq OWNER TO neondb_owner;

--
-- Name: borrowers_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.borrowers_id_seq OWNED BY public.borrowers.id;


--
-- Name: document; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.document (
    id integer NOT NULL,
    filename character varying(200) NOT NULL,
    document_type character varying(50) NOT NULL,
    ocr_status character varying(20) DEFAULT 'pending'::character varying,
    ocr_result jsonb,
    loan_id integer NOT NULL,
    uploaded_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    file_path character varying(200) DEFAULT ''::character varying NOT NULL,
    ocr_text text
);


ALTER TABLE public.document OWNER TO neondb_owner;

--
-- Name: document_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.document_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.document_id_seq OWNER TO neondb_owner;

--
-- Name: document_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.document_id_seq OWNED BY public.document.id;


--
-- Name: documents; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.documents (
    id integer NOT NULL,
    borrower_id integer,
    loan_id integer,
    document_type text NOT NULL,
    file_name text NOT NULL,
    file_url text NOT NULL,
    mime_type text NOT NULL,
    ocr_status text DEFAULT 'pending'::text NOT NULL,
    ocr_result jsonb,
    verification_status text DEFAULT 'pending'::text NOT NULL,
    verified_by integer,
    verified_at timestamp without time zone,
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone,
    file_path character varying(200) NOT NULL,
    ocr_text text,
    uploaded_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    application_id integer,
    extracted_data jsonb,
    user_id integer
);


ALTER TABLE public.documents OWNER TO neondb_owner;

--
-- Name: documents_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.documents_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.documents_id_seq OWNER TO neondb_owner;

--
-- Name: documents_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.documents_id_seq OWNED BY public.documents.id;


--
-- Name: employment_details; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.employment_details (
    id integer NOT NULL,
    loan_application_id integer NOT NULL,
    company_department character varying(200) NOT NULL,
    file_number character varying(50) NOT NULL,
    "position" character varying(100) NOT NULL,
    postal_address character varying(200) NOT NULL,
    phone character varying(20) NOT NULL,
    date_employed date NOT NULL,
    paymaster character varying(200) NOT NULL
);


ALTER TABLE public.employment_details OWNER TO neondb_owner;

--
-- Name: employment_details_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.employment_details_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.employment_details_id_seq OWNER TO neondb_owner;

--
-- Name: employment_details_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.employment_details_id_seq OWNED BY public.employment_details.id;


--
-- Name: financial_details; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.financial_details (
    id integer NOT NULL,
    loan_application_id integer NOT NULL,
    loan_amount numeric(10,2) NOT NULL,
    fortnightly_repayment numeric(10,2) NOT NULL,
    number_of_fortnights integer NOT NULL,
    total_loan_repayable numeric(10,2) NOT NULL,
    gross_salary numeric(10,2) NOT NULL,
    net_salary numeric(10,2) NOT NULL
);


ALTER TABLE public.financial_details OWNER TO neondb_owner;

--
-- Name: financial_details_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.financial_details_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.financial_details_id_seq OWNER TO neondb_owner;

--
-- Name: financial_details_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.financial_details_id_seq OWNED BY public.financial_details.id;


--
-- Name: loan; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.loan (
    id integer NOT NULL,
    amount numeric(10,2) NOT NULL,
    term integer NOT NULL,
    status character varying(20) DEFAULT 'pending'::character varying NOT NULL,
    purpose text NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    user_id integer NOT NULL,
    application_id integer
);


ALTER TABLE public.loan OWNER TO neondb_owner;

--
-- Name: loan_application; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.loan_application (
    id integer NOT NULL,
    user_id integer NOT NULL,
    status character varying(20) NOT NULL,
    signature_date timestamp without time zone NOT NULL,
    created_at timestamp without time zone NOT NULL
);


ALTER TABLE public.loan_application OWNER TO neondb_owner;

--
-- Name: loan_application_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.loan_application_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.loan_application_id_seq OWNER TO neondb_owner;

--
-- Name: loan_application_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.loan_application_id_seq OWNED BY public.loan_application.id;


--
-- Name: loan_break_up; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.loan_break_up (
    id integer NOT NULL,
    loan_application_id integer NOT NULL,
    loan_amount numeric(10,2) NOT NULL,
    existing_loan numeric(10,2) NOT NULL,
    net_loan_amount numeric(10,2) NOT NULL
);


ALTER TABLE public.loan_break_up OWNER TO neondb_owner;

--
-- Name: loan_break_up_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.loan_break_up_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.loan_break_up_id_seq OWNER TO neondb_owner;

--
-- Name: loan_break_up_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.loan_break_up_id_seq OWNED BY public.loan_break_up.id;


--
-- Name: loan_details; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.loan_details (
    id integer NOT NULL,
    loan_id integer NOT NULL,
    loan_type character varying(50) NOT NULL,
    interest_rate numeric(5,2) NOT NULL,
    processing_fee numeric(10,2),
    insurance_fee numeric(10,2),
    total_amount_payable numeric(10,2) NOT NULL,
    monthly_installment numeric(10,2) NOT NULL,
    start_date date,
    end_date date,
    disbursement_date timestamp without time zone,
    disbursement_method character varying(50),
    disbursement_status character varying(20) DEFAULT 'pending'::character varying,
    income_proof jsonb,
    expense_details jsonb,
    collateral_details jsonb
);


ALTER TABLE public.loan_details OWNER TO neondb_owner;

--
-- Name: loan_details_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.loan_details_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.loan_details_id_seq OWNER TO neondb_owner;

--
-- Name: loan_details_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.loan_details_id_seq OWNED BY public.loan_details.id;


--
-- Name: loan_funding_details; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.loan_funding_details (
    id integer NOT NULL,
    loan_application_id integer NOT NULL,
    bank character varying(100) NOT NULL,
    branch character varying(100) NOT NULL,
    bsb_code character varying(20) NOT NULL,
    account_name character varying(200) NOT NULL,
    account_number character varying(50) NOT NULL,
    account_type character varying(20) NOT NULL
);


ALTER TABLE public.loan_funding_details OWNER TO neondb_owner;

--
-- Name: loan_funding_details_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.loan_funding_details_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.loan_funding_details_id_seq OWNER TO neondb_owner;

--
-- Name: loan_funding_details_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.loan_funding_details_id_seq OWNED BY public.loan_funding_details.id;


--
-- Name: loan_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.loan_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.loan_id_seq OWNER TO neondb_owner;

--
-- Name: loan_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.loan_id_seq OWNED BY public.loan.id;


--
-- Name: loan_product; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.loan_product (
    id integer NOT NULL,
    loan_application_id integer NOT NULL,
    product_type character varying(50) NOT NULL,
    description text
);


ALTER TABLE public.loan_product OWNER TO neondb_owner;

--
-- Name: loan_product_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.loan_product_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.loan_product_id_seq OWNER TO neondb_owner;

--
-- Name: loan_product_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.loan_product_id_seq OWNED BY public.loan_product.id;


--
-- Name: loans; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.loans (
    id integer NOT NULL,
    borrower_id integer,
    amount numeric NOT NULL,
    term integer NOT NULL,
    interest_rate numeric NOT NULL,
    status text NOT NULL,
    purpose text NOT NULL,
    created_at timestamp without time zone DEFAULT now(),
    approved_by integer,
    approved_at timestamp without time zone
);


ALTER TABLE public.loans OWNER TO neondb_owner;

--
-- Name: loans_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.loans_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.loans_id_seq OWNER TO neondb_owner;

--
-- Name: loans_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.loans_id_seq OWNED BY public.loans.id;


--
-- Name: payments; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.payments (
    id integer NOT NULL,
    loan_id integer,
    amount numeric NOT NULL,
    payment_date timestamp without time zone NOT NULL,
    status text NOT NULL,
    created_at timestamp without time zone DEFAULT now()
);


ALTER TABLE public.payments OWNER TO neondb_owner;

--
-- Name: payments_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.payments_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.payments_id_seq OWNER TO neondb_owner;

--
-- Name: payments_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.payments_id_seq OWNED BY public.payments.id;


--
-- Name: personal_details; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.personal_details (
    id integer NOT NULL,
    loan_application_id integer NOT NULL,
    date_of_birth date NOT NULL,
    gender character varying(1) NOT NULL,
    mobile_number character varying(20) NOT NULL,
    email character varying(120) NOT NULL,
    village character varying(100) NOT NULL,
    district character varying(100) NOT NULL,
    province character varying(100) NOT NULL,
    nationality character varying(100) NOT NULL,
    surname character varying(100) NOT NULL,
    given_name character varying(100) NOT NULL
);


ALTER TABLE public.personal_details OWNER TO neondb_owner;

--
-- Name: personal_details_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.personal_details_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.personal_details_id_seq OWNER TO neondb_owner;

--
-- Name: personal_details_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.personal_details_id_seq OWNED BY public.personal_details.id;


--
-- Name: repayment_record; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.repayment_record (
    id integer NOT NULL,
    loan_id integer NOT NULL,
    amount_paid numeric(10,2) NOT NULL,
    payment_date timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    payment_method character varying(50),
    transaction_id character varying(100),
    payment_status character varying(20) DEFAULT 'completed'::character varying,
    receipt_number character varying(50),
    notes text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.repayment_record OWNER TO neondb_owner;

--
-- Name: repayment_record_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.repayment_record_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.repayment_record_id_seq OWNER TO neondb_owner;

--
-- Name: repayment_record_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.repayment_record_id_seq OWNED BY public.repayment_record.id;


--
-- Name: repayment_records; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.repayment_records (
    id integer NOT NULL,
    loan_id integer NOT NULL,
    amount numeric(10,2) NOT NULL,
    payment_date timestamp without time zone NOT NULL,
    due_date timestamp without time zone NOT NULL,
    is_late_payment boolean,
    created_at timestamp without time zone
);


ALTER TABLE public.repayment_records OWNER TO neondb_owner;

--
-- Name: repayment_records_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.repayment_records_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.repayment_records_id_seq OWNER TO neondb_owner;

--
-- Name: repayment_records_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.repayment_records_id_seq OWNED BY public.repayment_records.id;


--
-- Name: repayments; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.repayments (
    id integer NOT NULL,
    loan_id integer NOT NULL,
    payment_number character varying(20),
    amount_paid numeric(10,2) NOT NULL,
    payment_date timestamp without time zone NOT NULL,
    due_date timestamp without time zone NOT NULL,
    payment_method character varying(50) NOT NULL,
    transaction_id character varying(100),
    payment_status character varying(20),
    receipt_number character varying(50),
    notes text,
    principal_amount numeric(10,2) NOT NULL,
    interest_amount numeric(10,2) NOT NULL,
    late_fee numeric(10,2),
    total_paid numeric(10,2),
    payment_period character varying(20),
    is_late_payment boolean,
    days_late integer,
    outstanding_balance numeric(10,2),
    ocr_verified boolean,
    ocr_confidence_score double precision,
    ocr_extracted_data json,
    receipt_image_path character varying(255),
    last_ocr_update timestamp without time zone,
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    created_by integer
);


ALTER TABLE public.repayments OWNER TO neondb_owner;

--
-- Name: repayments_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.repayments_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.repayments_id_seq OWNER TO neondb_owner;

--
-- Name: repayments_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.repayments_id_seq OWNED BY public.repayments.id;


--
-- Name: residential_address; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.residential_address (
    id integer NOT NULL,
    loan_application_id integer NOT NULL,
    lot character varying(50) NOT NULL,
    section character varying(50) NOT NULL,
    suburb character varying(100) NOT NULL,
    street_name character varying(200) NOT NULL,
    marital_status character varying(20) NOT NULL,
    spouse_last_name character varying(100),
    spouse_first_name character varying(100),
    spouse_employer_name character varying(200),
    spouse_contact character varying(20)
);


ALTER TABLE public.residential_address OWNER TO neondb_owner;

--
-- Name: residential_address_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.residential_address_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.residential_address_id_seq OWNER TO neondb_owner;

--
-- Name: residential_address_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.residential_address_id_seq OWNED BY public.residential_address.id;


--
-- Name: user; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public."user" (
    id integer NOT NULL,
    client_number character varying(10) NOT NULL,
    username character varying(80) NOT NULL,
    email character varying(120) NOT NULL,
    full_name character varying(200) NOT NULL,
    password_hash character varying(255) NOT NULL,
    phone_number character varying(20),
    address character varying(200),
    department character varying(50),
    is_application_created boolean DEFAULT false,
    password_changed boolean DEFAULT false,
    role character varying(20) DEFAULT 'borrower'::character varying NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


ALTER TABLE public."user" OWNER TO neondb_owner;

--
-- Name: user_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.user_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.user_id_seq OWNER TO neondb_owner;

--
-- Name: user_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.user_id_seq OWNED BY public."user".id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.users (
    id integer NOT NULL,
    username text NOT NULL,
    password text NOT NULL,
    role text NOT NULL,
    email text NOT NULL,
    full_name text NOT NULL,
    created_at timestamp without time zone DEFAULT now(),
    permissions json DEFAULT '["view"]'::json,
    last_login_at timestamp without time zone,
    status text DEFAULT 'active'::text NOT NULL,
    dashboard_preferences jsonb DEFAULT '{}'::jsonb
);


ALTER TABLE public.users OWNER TO neondb_owner;

--
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.users_id_seq OWNER TO neondb_owner;

--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- Name: analytics id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.analytics ALTER COLUMN id SET DEFAULT nextval('public.analytics_id_seq'::regclass);


--
-- Name: borrower id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.borrower ALTER COLUMN id SET DEFAULT nextval('public.borrower_id_seq'::regclass);


--
-- Name: borrower_details id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.borrower_details ALTER COLUMN id SET DEFAULT nextval('public.borrower_details_id_seq'::regclass);


--
-- Name: borrowers id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.borrowers ALTER COLUMN id SET DEFAULT nextval('public.borrowers_id_seq'::regclass);


--
-- Name: document id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.document ALTER COLUMN id SET DEFAULT nextval('public.document_id_seq'::regclass);


--
-- Name: documents id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.documents ALTER COLUMN id SET DEFAULT nextval('public.documents_id_seq'::regclass);


--
-- Name: employment_details id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.employment_details ALTER COLUMN id SET DEFAULT nextval('public.employment_details_id_seq'::regclass);


--
-- Name: financial_details id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.financial_details ALTER COLUMN id SET DEFAULT nextval('public.financial_details_id_seq'::regclass);


--
-- Name: loan id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.loan ALTER COLUMN id SET DEFAULT nextval('public.loan_id_seq'::regclass);


--
-- Name: loan_application id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.loan_application ALTER COLUMN id SET DEFAULT nextval('public.loan_application_id_seq'::regclass);


--
-- Name: loan_break_up id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.loan_break_up ALTER COLUMN id SET DEFAULT nextval('public.loan_break_up_id_seq'::regclass);


--
-- Name: loan_details id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.loan_details ALTER COLUMN id SET DEFAULT nextval('public.loan_details_id_seq'::regclass);


--
-- Name: loan_funding_details id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.loan_funding_details ALTER COLUMN id SET DEFAULT nextval('public.loan_funding_details_id_seq'::regclass);


--
-- Name: loan_product id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.loan_product ALTER COLUMN id SET DEFAULT nextval('public.loan_product_id_seq'::regclass);


--
-- Name: loans id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.loans ALTER COLUMN id SET DEFAULT nextval('public.loans_id_seq'::regclass);


--
-- Name: payments id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.payments ALTER COLUMN id SET DEFAULT nextval('public.payments_id_seq'::regclass);


--
-- Name: personal_details id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.personal_details ALTER COLUMN id SET DEFAULT nextval('public.personal_details_id_seq'::regclass);


--
-- Name: repayment_record id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.repayment_record ALTER COLUMN id SET DEFAULT nextval('public.repayment_record_id_seq'::regclass);


--
-- Name: repayment_records id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.repayment_records ALTER COLUMN id SET DEFAULT nextval('public.repayment_records_id_seq'::regclass);


--
-- Name: repayments id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.repayments ALTER COLUMN id SET DEFAULT nextval('public.repayments_id_seq'::regclass);


--
-- Name: residential_address id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.residential_address ALTER COLUMN id SET DEFAULT nextval('public.residential_address_id_seq'::regclass);


--
-- Name: user id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public."user" ALTER COLUMN id SET DEFAULT nextval('public.user_id_seq'::regclass);


--
-- Name: users id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- Data for Name: alembic_version; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.alembic_version (version_num) FROM stdin;
\.


--
-- Data for Name: analytics; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.analytics (id, metric_type, metric_value, dimension, dimension_value, created_at) FROM stdin;
\.


--
-- Data for Name: borrower; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.borrower (id, user_id, phone_number, address, employment_status, monthly_income, created_at) FROM stdin;
\.


--
-- Data for Name: borrower_details; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.borrower_details (id, user_id, marital_status, dependents, education, employment_type, income_source, monthly_income, other_income, existing_loans, credit_score, created_at, updated_at, identification_number, tax_id, employer_details, bank_details, reference_details) FROM stdin;
\.


--
-- Data for Name: borrowers; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.borrowers (id, user_id, phone_number, address, employment_status, monthly_income, created_at) FROM stdin;
\.


--
-- Data for Name: document; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.document (id, filename, document_type, ocr_status, ocr_result, loan_id, uploaded_at, file_path, ocr_text) FROM stdin;
\.


--
-- Data for Name: documents; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.documents (id, borrower_id, loan_id, document_type, file_name, file_url, mime_type, ocr_status, ocr_result, verification_status, verified_by, verified_at, created_at, updated_at, file_path, ocr_text, uploaded_at, application_id, extracted_data, user_id) FROM stdin;
\.


--
-- Data for Name: employment_details; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.employment_details (id, loan_application_id, company_department, file_number, "position", postal_address, phone, date_employed, paymaster) FROM stdin;
\.


--
-- Data for Name: financial_details; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.financial_details (id, loan_application_id, loan_amount, fortnightly_repayment, number_of_fortnights, total_loan_repayable, gross_salary, net_salary) FROM stdin;
\.


--
-- Data for Name: loan; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.loan (id, amount, term, status, purpose, created_at, user_id, application_id) FROM stdin;
\.


--
-- Data for Name: loan_application; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.loan_application (id, user_id, status, signature_date, created_at) FROM stdin;
\.


--
-- Data for Name: loan_break_up; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.loan_break_up (id, loan_application_id, loan_amount, existing_loan, net_loan_amount) FROM stdin;
\.


--
-- Data for Name: loan_details; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.loan_details (id, loan_id, loan_type, interest_rate, processing_fee, insurance_fee, total_amount_payable, monthly_installment, start_date, end_date, disbursement_date, disbursement_method, disbursement_status, income_proof, expense_details, collateral_details) FROM stdin;
\.


--
-- Data for Name: loan_funding_details; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.loan_funding_details (id, loan_application_id, bank, branch, bsb_code, account_name, account_number, account_type) FROM stdin;
\.


--
-- Data for Name: loan_product; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.loan_product (id, loan_application_id, product_type, description) FROM stdin;
\.


--
-- Data for Name: loans; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.loans (id, borrower_id, amount, term, interest_rate, status, purpose, created_at, approved_by, approved_at) FROM stdin;
\.


--
-- Data for Name: payments; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.payments (id, loan_id, amount, payment_date, status, created_at) FROM stdin;
\.


--
-- Data for Name: personal_details; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.personal_details (id, loan_application_id, date_of_birth, gender, mobile_number, email, village, district, province, nationality, surname, given_name) FROM stdin;
\.


--
-- Data for Name: repayment_record; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.repayment_record (id, loan_id, amount_paid, payment_date, payment_method, transaction_id, payment_status, receipt_number, notes, created_at) FROM stdin;
\.


--
-- Data for Name: repayment_records; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.repayment_records (id, loan_id, amount, payment_date, due_date, is_late_payment, created_at) FROM stdin;
\.


--
-- Data for Name: repayments; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.repayments (id, loan_id, payment_number, amount_paid, payment_date, due_date, payment_method, transaction_id, payment_status, receipt_number, notes, principal_amount, interest_amount, late_fee, total_paid, payment_period, is_late_payment, days_late, outstanding_balance, ocr_verified, ocr_confidence_score, ocr_extracted_data, receipt_image_path, last_ocr_update, created_at, updated_at, created_by) FROM stdin;
\.


--
-- Data for Name: residential_address; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.residential_address (id, loan_application_id, lot, section, suburb, street_name, marital_status, spouse_last_name, spouse_first_name, spouse_employer_name, spouse_contact) FROM stdin;
\.


--
-- Data for Name: user; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public."user" (id, client_number, username, email, full_name, password_hash, phone_number, address, department, is_application_created, password_changed, role, created_at) FROM stdin;
1	KNRFS00001	DevAdmin	admin@knrfinancial.com	System Administrator	scrypt:32768:8:1$PYuZ9F5DbUphqMo6$d9f6f41be3c5f84f327b8299de04b3e513399720495353615a3e3bb86fab0cf1d3cdfcd87922461dc349bb782e196c1088ba570a8f11ae501b6878090346f933	\N	\N	\N	f	f	admin	2024-12-13 05:45:56.234492
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.users (id, username, password, role, email, full_name, created_at, permissions, last_login_at, status, dashboard_preferences) FROM stdin;
\.


--
-- Name: analytics_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.analytics_id_seq', 1, false);


--
-- Name: borrower_details_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.borrower_details_id_seq', 1, false);


--
-- Name: borrower_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.borrower_id_seq', 1, false);


--
-- Name: borrowers_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.borrowers_id_seq', 1, false);


--
-- Name: document_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.document_id_seq', 1, false);


--
-- Name: documents_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.documents_id_seq', 19, true);


--
-- Name: employment_details_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.employment_details_id_seq', 1, false);


--
-- Name: financial_details_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.financial_details_id_seq', 1, false);


--
-- Name: loan_application_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.loan_application_id_seq', 1, false);


--
-- Name: loan_break_up_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.loan_break_up_id_seq', 1, false);


--
-- Name: loan_details_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.loan_details_id_seq', 1, false);


--
-- Name: loan_funding_details_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.loan_funding_details_id_seq', 1, false);


--
-- Name: loan_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.loan_id_seq', 1, false);


--
-- Name: loan_product_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.loan_product_id_seq', 1, false);


--
-- Name: loans_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.loans_id_seq', 1, false);


--
-- Name: payments_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.payments_id_seq', 1, false);


--
-- Name: personal_details_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.personal_details_id_seq', 1, false);


--
-- Name: repayment_record_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.repayment_record_id_seq', 1, false);


--
-- Name: repayment_records_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.repayment_records_id_seq', 1, false);


--
-- Name: repayments_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.repayments_id_seq', 1, false);


--
-- Name: residential_address_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.residential_address_id_seq', 1, false);


--
-- Name: user_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.user_id_seq', 1, true);


--
-- Name: users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.users_id_seq', 1, false);


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: analytics analytics_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.analytics
    ADD CONSTRAINT analytics_pkey PRIMARY KEY (id);


--
-- Name: borrower_details borrower_details_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.borrower_details
    ADD CONSTRAINT borrower_details_pkey PRIMARY KEY (id);


--
-- Name: borrower borrower_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.borrower
    ADD CONSTRAINT borrower_pkey PRIMARY KEY (id);


--
-- Name: borrowers borrowers_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.borrowers
    ADD CONSTRAINT borrowers_pkey PRIMARY KEY (id);


--
-- Name: document document_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.document
    ADD CONSTRAINT document_pkey PRIMARY KEY (id);


--
-- Name: documents documents_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.documents
    ADD CONSTRAINT documents_pkey PRIMARY KEY (id);


--
-- Name: employment_details employment_details_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.employment_details
    ADD CONSTRAINT employment_details_pkey PRIMARY KEY (id);


--
-- Name: financial_details financial_details_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.financial_details
    ADD CONSTRAINT financial_details_pkey PRIMARY KEY (id);


--
-- Name: loan_application loan_application_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.loan_application
    ADD CONSTRAINT loan_application_pkey PRIMARY KEY (id);


--
-- Name: loan_break_up loan_break_up_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.loan_break_up
    ADD CONSTRAINT loan_break_up_pkey PRIMARY KEY (id);


--
-- Name: loan_details loan_details_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.loan_details
    ADD CONSTRAINT loan_details_pkey PRIMARY KEY (id);


--
-- Name: loan_funding_details loan_funding_details_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.loan_funding_details
    ADD CONSTRAINT loan_funding_details_pkey PRIMARY KEY (id);


--
-- Name: loan loan_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.loan
    ADD CONSTRAINT loan_pkey PRIMARY KEY (id);


--
-- Name: loan_product loan_product_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.loan_product
    ADD CONSTRAINT loan_product_pkey PRIMARY KEY (id);


--
-- Name: loans loans_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.loans
    ADD CONSTRAINT loans_pkey PRIMARY KEY (id);


--
-- Name: payments payments_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.payments
    ADD CONSTRAINT payments_pkey PRIMARY KEY (id);


--
-- Name: personal_details personal_details_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.personal_details
    ADD CONSTRAINT personal_details_pkey PRIMARY KEY (id);


--
-- Name: repayment_record repayment_record_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.repayment_record
    ADD CONSTRAINT repayment_record_pkey PRIMARY KEY (id);


--
-- Name: repayment_records repayment_records_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.repayment_records
    ADD CONSTRAINT repayment_records_pkey PRIMARY KEY (id);


--
-- Name: repayments repayments_payment_number_key; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.repayments
    ADD CONSTRAINT repayments_payment_number_key UNIQUE (payment_number);


--
-- Name: repayments repayments_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.repayments
    ADD CONSTRAINT repayments_pkey PRIMARY KEY (id);


--
-- Name: repayments repayments_receipt_number_key; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.repayments
    ADD CONSTRAINT repayments_receipt_number_key UNIQUE (receipt_number);


--
-- Name: repayments repayments_transaction_id_key; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.repayments
    ADD CONSTRAINT repayments_transaction_id_key UNIQUE (transaction_id);


--
-- Name: residential_address residential_address_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.residential_address
    ADD CONSTRAINT residential_address_pkey PRIMARY KEY (id);


--
-- Name: user user_client_number_key; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public."user"
    ADD CONSTRAINT user_client_number_key UNIQUE (client_number);


--
-- Name: user user_email_key; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public."user"
    ADD CONSTRAINT user_email_key UNIQUE (email);


--
-- Name: user user_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public."user"
    ADD CONSTRAINT user_pkey PRIMARY KEY (id);


--
-- Name: user user_username_key; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public."user"
    ADD CONSTRAINT user_username_key UNIQUE (username);


--
-- Name: users users_email_unique; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_email_unique UNIQUE (email);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: users users_username_unique; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_username_unique UNIQUE (username);


--
-- Name: borrower_details borrower_details_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.borrower_details
    ADD CONSTRAINT borrower_details_user_id_fkey FOREIGN KEY (user_id) REFERENCES public."user"(id);


--
-- Name: borrowers borrowers_user_id_users_id_fk; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.borrowers
    ADD CONSTRAINT borrowers_user_id_users_id_fk FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: document document_loan_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.document
    ADD CONSTRAINT document_loan_id_fkey FOREIGN KEY (loan_id) REFERENCES public.loan(id) ON DELETE CASCADE;


--
-- Name: documents documents_application_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.documents
    ADD CONSTRAINT documents_application_id_fkey FOREIGN KEY (application_id) REFERENCES public.loan_application(id);


--
-- Name: documents documents_borrower_id_borrowers_id_fk; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.documents
    ADD CONSTRAINT documents_borrower_id_borrowers_id_fk FOREIGN KEY (borrower_id) REFERENCES public.borrowers(id);


--
-- Name: documents documents_loan_id_loans_id_fk; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.documents
    ADD CONSTRAINT documents_loan_id_loans_id_fk FOREIGN KEY (loan_id) REFERENCES public.loans(id);


--
-- Name: documents documents_verified_by_users_id_fk; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.documents
    ADD CONSTRAINT documents_verified_by_users_id_fk FOREIGN KEY (verified_by) REFERENCES public.users(id);


--
-- Name: employment_details employment_details_loan_application_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.employment_details
    ADD CONSTRAINT employment_details_loan_application_id_fkey FOREIGN KEY (loan_application_id) REFERENCES public.loan_application(id);


--
-- Name: financial_details financial_details_loan_application_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.financial_details
    ADD CONSTRAINT financial_details_loan_application_id_fkey FOREIGN KEY (loan_application_id) REFERENCES public.loan_application(id);


--
-- Name: loan loan_application_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.loan
    ADD CONSTRAINT loan_application_id_fkey FOREIGN KEY (application_id) REFERENCES public.loan_application(id);


--
-- Name: loan_break_up loan_break_up_loan_application_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.loan_break_up
    ADD CONSTRAINT loan_break_up_loan_application_id_fkey FOREIGN KEY (loan_application_id) REFERENCES public.loan_application(id);


--
-- Name: loan_details loan_details_loan_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.loan_details
    ADD CONSTRAINT loan_details_loan_id_fkey FOREIGN KEY (loan_id) REFERENCES public.loan(id);


--
-- Name: loan_funding_details loan_funding_details_loan_application_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.loan_funding_details
    ADD CONSTRAINT loan_funding_details_loan_application_id_fkey FOREIGN KEY (loan_application_id) REFERENCES public.loan_application(id);


--
-- Name: loan_product loan_product_loan_application_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.loan_product
    ADD CONSTRAINT loan_product_loan_application_id_fkey FOREIGN KEY (loan_application_id) REFERENCES public.loan_application(id);


--
-- Name: loans loans_approved_by_users_id_fk; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.loans
    ADD CONSTRAINT loans_approved_by_users_id_fk FOREIGN KEY (approved_by) REFERENCES public.users(id);


--
-- Name: loans loans_borrower_id_borrowers_id_fk; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.loans
    ADD CONSTRAINT loans_borrower_id_borrowers_id_fk FOREIGN KEY (borrower_id) REFERENCES public.borrowers(id);


--
-- Name: payments payments_loan_id_loans_id_fk; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.payments
    ADD CONSTRAINT payments_loan_id_loans_id_fk FOREIGN KEY (loan_id) REFERENCES public.loans(id);


--
-- Name: personal_details personal_details_loan_application_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.personal_details
    ADD CONSTRAINT personal_details_loan_application_id_fkey FOREIGN KEY (loan_application_id) REFERENCES public.loan_application(id);


--
-- Name: repayment_record repayment_record_loan_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.repayment_record
    ADD CONSTRAINT repayment_record_loan_id_fkey FOREIGN KEY (loan_id) REFERENCES public.loan(id);


--
-- Name: repayment_records repayment_records_loan_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.repayment_records
    ADD CONSTRAINT repayment_records_loan_id_fkey FOREIGN KEY (loan_id) REFERENCES public.loans(id);


--
-- Name: repayments repayments_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.repayments
    ADD CONSTRAINT repayments_created_by_fkey FOREIGN KEY (created_by) REFERENCES public."user"(id);


--
-- Name: repayments repayments_loan_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.repayments
    ADD CONSTRAINT repayments_loan_id_fkey FOREIGN KEY (loan_id) REFERENCES public.loans(id);


--
-- Name: residential_address residential_address_loan_application_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.residential_address
    ADD CONSTRAINT residential_address_loan_application_id_fkey FOREIGN KEY (loan_application_id) REFERENCES public.loan_application(id);


--
-- Name: DEFAULT PRIVILEGES FOR SEQUENCES; Type: DEFAULT ACL; Schema: public; Owner: cloud_admin
--

ALTER DEFAULT PRIVILEGES FOR ROLE cloud_admin IN SCHEMA public GRANT ALL ON SEQUENCES TO neon_superuser WITH GRANT OPTION;


--
-- Name: DEFAULT PRIVILEGES FOR TABLES; Type: DEFAULT ACL; Schema: public; Owner: cloud_admin
--

ALTER DEFAULT PRIVILEGES FOR ROLE cloud_admin IN SCHEMA public GRANT ALL ON TABLES TO neon_superuser WITH GRANT OPTION;


--
-- PostgreSQL database dump complete
--


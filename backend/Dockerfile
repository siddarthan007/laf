FROM public.ecr.aws/lambda/python:3.12

# Install system dependencies
# pgvector and pillow might need build tools
RUN dnf install -y gcc python3-devel postgresql-devel && \
    dnf clean all

# Copy requirements
COPY pyproject.toml README.md .

# Install CPU-only torch first to avoid downloading CUDA libs
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# Install dependencies
# We use pip to install from pyproject.toml
# We need to install mangum for Lambda adapter
RUN pip install --no-cache-dir . mangum

# Copy application code
COPY app/ ${LAMBDA_TASK_ROOT}/app
COPY static/ ${LAMBDA_TASK_ROOT}/static
COPY alembic/ ${LAMBDA_TASK_ROOT}/alembic
COPY alembic.ini ${LAMBDA_TASK_ROOT}/alembic.ini
COPY lambda_handler.py ${LAMBDA_TASK_ROOT}/lambda_handler.py

# Set the CMD to your handler
CMD [ "lambda_handler.handler" ]

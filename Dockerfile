FROM python:3.11-slim

RUN echo "test" > /test.txt

CMD ["cat", "/test.txt"]

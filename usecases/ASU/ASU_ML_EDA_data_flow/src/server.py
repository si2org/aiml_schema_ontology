import grpc
from concurrent import futures
import os
import data_service_pb2
import data_service_pb2_grpc

class DataService(data_service_pb2_grpc.DataServiceServicer):
    def GetFile(self, request, context):
        file_path = request.file_path
        if not os.path.exists(file_path):
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details("File not found")
            return
        
        with open(file_path, "rb") as f:
            while chunk := f.read(4096):  # Send in 4KB chunks
                yield data_service_pb2.FileChunk(content=chunk)

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    data_service_pb2_grpc.add_DataServiceServicer_to_server(DataService(), server)
    server.add_insecure_port("[::]:50051")
    server.start()
    server.wait_for_termination()

if __name__ == "__main__":
    serve()


import time
from json import dumps, loads
import requests


class Client:
    def __init__(self):
        self.url = "http://localhost:8080"

    def request_job(self):
        request = requests.get(self.url)
        if request.status_code // 100 == 4:
            request.raise_for_status()
        work_id, work = list(loads(request.text).items())[0]
        return work_id, work


    def handle_error(self, j_id, work):
        while j_id == "error":
            print(work)
            print("I'm sleeping a minute.")
            time.sleep(60)
            j_id, work = self.request_job(self.url)
        return j_id, work


    def get_job(self):
        full_url = f"{self.url}/get_job"
        j_id, work = self.request_job()
        if j_id == "error":
            j_id, work = self.handle_error(j_id, work)
        return j_id, work


    def perform_job(self, j):
        print(f"I am working for {j} seconds.")
        time.sleep(int(j))


    def send_job_results(self, j_id, job_result):
        end_point = "/put_results"
        data = {j_id: int(job_result)}
        request = requests.put(self.url + end_point, data=dumps(data))
        request.raise_for_status()


    def read_client_id(self):
        try:
            with open("client.cfg", "r") as file:
                return int(file.readline())
        except FileNotFoundError:
            return -1


    def write_client_id(self, c_id):
        with open("client.cfg", "w") as file:
            file.write(str(c_id))


    def request_client_id(self):
        end_point = "/get_client_id"
        request = requests.get(self.url + end_point)

        # Check if status code is 200 type code: successful GET
        if request.status_code // 100 == 2:
            c_id = int(request.json())
            self.write_client_id(c_id)
            return c_id
        return -1


    # Reads from file, or requests if nothing there
    def get_client_id(self):
        c_id = self.read_client_id()
        if c_id == -1:
            c_id = self.request_client_id()
        if c_id == -1:
            print("Could not get client ID!")
        return c_id


    def complete_client_request(self):
        job_id, job = self.get_job()
        self.perform_job(job)
        self.send_job_results(job_id, job)



if __name__ == "__main__":
    client = Client()
    client_id = client.get_client_id()
    print("ID of this client: ", client_id)

    while True:
        client.complete_client_request()

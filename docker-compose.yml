services:
  mssql:
    image: mcr.microsoft.com/mssql/server:2022-latest
    container_name: mssql-dev
    ports:
      - "1433:1433"
    environment:
      ACCEPT_EULA: "Y"
      MSSQL_SA_PASSWORD: "Passw0rd_str0ng!"
      MSSQL_PID: "Developer"   # Express にしたい場合は "Express"
    volumes:
      - mssql_data:/var/opt/mssql  # DBを永続化

volumes:
  mssql_data:

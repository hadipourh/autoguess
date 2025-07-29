# Please install docker according to the guideline provided here: https://docs.docker.com/engine/install/ubuntu/

FROM debian:latest
ARG DEBIAN_FRONTEND=noninteractive

# Install some basic packages
RUN apt-get update && apt-get install -y build-essential git cmake wget curl python3 python3-pip python3-dev python3-full

# Install the latest version of MiniZinc
WORKDIR  /home/tools/
RUN LATEST_MINIZINC_VERSION=$(curl -s https://api.github.com/repos/MiniZinc/MiniZincIDE/releases/latest | grep -oP '"tag_name": "\K(.*)(?=")') \
    && wget "https://github.com/MiniZinc/MiniZincIDE/releases/download/$LATEST_MINIZINC_VERSION/MiniZincIDE-$LATEST_MINIZINC_VERSION-bundle-linux-x86_64.tgz" \
    && mkdir MiniZinc \
    && tar -xvzf "MiniZincIDE-$LATEST_MINIZINC_VERSION-bundle-linux-x86_64.tgz" -C MiniZinc --strip-components=1 \
    && rm "MiniZincIDE-$LATEST_MINIZINC_VERSION-bundle-linux-x86_64.tgz"
RUN ln -s /home/tools/MiniZinc/bin/minizinc /usr/local/bin/minizinc

# Clone Autoguess
RUN git clone https://github.com/hadipourh/autoguess
WORKDIR /home/tools/autoguess

# # Install Or-Tools and link it to MiniZinc (This is not necessary for versions of MiniZinc >= 2.8.1)
# WORKDIR /home/tools/
# RUN wget https://github.com/google/or-tools/releases/download/v9.2/or-tools_amd64_flatzinc_debian-11_v9.2.9972.tar.gz && \ 
#     mkdir or-tools && \
#     tar xvzf or-tools_amd64_flatzinc_debian-11_v9.2.9972.tar.gz -C or-tools --strip-components=1 && \
#     rm or-tools_amd64_flatzinc_debian-11_v9.2.9972.tar.gz && \
#     cp configfiles/ortools.msc /home/tools/MiniZinc/share/minizinc/solvers

# Install SageMath
RUN apt-get install -y sagemath

# Install Graphviz
RUN apt-get install -y graphviz

# Create and activate a virtual environment
RUN python3 -m venv venv

# Install python-sat
RUN venv/bin/python3 -m pip install python-sat[pblib,aiger]

# Install pysmt
RUN venv/bin/python3 -m pip install pysmt

# Install smt solvers supported by pysmt
RUN venv/bin/python3 -m pip install cython
# RUN yes | venv/bin/python3 -m pysmt install --btor (Boolector has been archived, and its developers have officially stopped maintaining it.)
RUN yes | venv/bin/python3 -m pysmt install --z3

# Install Z3 solver
RUN venv/bin/python3 -m pip install z3-solver

# Install Python interface of MiniZinc
RUN venv/bin/python3 -m pip install minizinc

# Install Gurobi (Restricted license - for non-production use only)
RUN venv/bin/python3 -m pip install gurobipy

# Install Python interface of Graphviz
RUN venv/bin/python3 -m pip install graphviz

# Install dot2tex
RUN venv/bin/python3 -m pip install dot2tex

# Clean up
RUN apt-get clean && rm -rf /var/lib/apt/lists/*

# Set the default command to run when a container starts
CMD cd /home/tools/autoguess && . venv/bin/activate && /bin/bash
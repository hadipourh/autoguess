# Please install docker according to the guideline provided here: https://docs.docker.com/engine/install/ubuntu/

FROM debian:latest
ARG DEBIAN_FRONTEND=noninteractive

# Install some basic packages
RUN apt-get update && apt-get install -y build-essential git cmake wget curl python3 python3-pip python3-dev

# Install python-sat
RUN python3 -m pip install python-sat[pblib,aiger]

# Install pysmt
RUN python3 -m pip install pysmt

# Install smt solvers supported by pysmt
RUN python3 -m pip install cython
RUN yes | python3 -m pysmt install --btor
RUN yes | python3 -m pysmt install --z3

# Install Z3 solver
RUN python3 -m pip install z3-solver

# Install MiniZinc
WORKDIR  /home/tools/
RUN wget https://github.com/MiniZinc/MiniZincIDE/releases/download/2.5.5/MiniZincIDE-2.5.5-bundle-linux-x86_64.tgz && \
    mkdir MiniZinc && \
    tar zxvf MiniZincIDE-2.5.5-bundle-linux-x86_64.tgz -C MiniZinc --strip-components=1 && \
    rm MiniZincIDE-2.5.5-bundle-linux-x86_64.tgz
RUN ln -s /home/tools/MiniZinc/bin/minizinc /usr/local/bin/minizinc

# Install Python interface of MiniZinc
RUN python3 -m pip install minizinc

# Install Or-Tools
WORKDIR /home/tools/
RUN wget https://github.com/google/or-tools/releases/download/v8.2/or-tools_flatzinc_debian-10_v8.2.8710.tar.gz && \ 
    mkdir or-tools && \
    tar xvzf or-tools_flatzinc_debian-10_v8.2.8710.tar.gz -C or-tools --strip-components=1 && \
    rm or-tools_flatzinc_debian-10_v8.2.8710.tar.gz

# Install Gurobi (Restricted license - for non-production use only)
RUN python3 -m pip install gurobipy

# Install SageMath
RUN apt-get install -y sagemath

# Install Graphviz
RUN apt-get install -y graphviz

# Install Python interface of Graphviz
RUN python3 -m pip install graphviz

# Install dot2tex
RUN python3 -m pip install dot2tex

# Clone Autoguess and introduce Or-Tools to MiniZinc
RUN git clone https://github.com/hadipourh/autoguess
WORKDIR /home/tools/autoguess
RUN cp configfiles/ortools.msc /home/tools/MiniZinc/share/minizinc/solvers

# Clean
RUN apt-get clean && rm -rf /var/lib/apt/lists/*

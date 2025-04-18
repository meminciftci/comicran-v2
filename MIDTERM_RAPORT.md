\documentclass[a4paper,12pt]{report}
\usepackage{styles/fbe_tez}
\usepackage[utf8x]{inputenc} % To use Unicode (e.g. Turkish) characters
\renewcommand{\labelenumi}{(\roman{enumi})}
\usepackage{amsmath, amsthm, amssymb}
 % Some extra symbols
\usepackage[bottom]{footmisc}
\usepackage{cite}
\usepackage{url}
\usepackage{graphicx}
\usepackage{longtable}
\graphicspath{{figures/}} % Graphics will be here

\usepackage{multirow}
\usepackage{subfigure}
\usepackage{algorithm}
\usepackage{algorithmic}

\begin{document}

% Title Page
\title{CMPE 492 \\ COMIC-RAN: Container-based Migration in C-RAN Implementation}
\author{
Furkan Şenkal \\
Muhammet Emin Çiftçi \\ \\
Advisor: \\ 
Tuna Tuğcu
}
\date{}
\maketitle{}
\pagenumbering{roman}
\tableofcontents

\chapter{INTRODUCTION}
\pagenumbering{arabic}

 In today's world, cellular communication has become one of the most significant technologies that provides wireless communication to wide areas. Therefore, advancements in the cellular network infrastructures have become more demanded by users, which resulted in the development of next generation technologies such as 5G. The shift from 4G to 5G has created the opportunity to take advantage of new architectures, one of which is Cloud Radio Access Networks (Cloud-RAN). The solution provided by Cloud-RAN tries to satisfy the high amount of resource need due to the increasing number of users. This project aims to focus on Cloud-RAN technology, its benefits, and possible improvements to it. In order to understand the importance of Cloud-RAN, first let us distinguish its functionalities compared to its ancestors.

 The initial Radio Access Networks (RAN) model consisted of two main parts: Remote Radio Head(RRH) and Base Band Unit(BBU). This model introduced issues such as increase in hardware resources in new demanding areas. Both BBU and RRH needed to be deployed to areas in order to make the operation possible. Elasticity of the infrastructure was quite low compared to the current system, Cloud-RAN. With the introduction of Cloud-RAN, BBUs are no more required to be deployed with their respected RRHs. The virtualization and centralization of BBUs allow cellular networks to be more efficient and scalable. 

 Our project aims to achieve live migration of processes between different virtual machines by using the current hand-off(hand-over) protocols with minimum modification. Previous method included containerization of processes in order to migrate them from one virtual machine to another. The method used post-copy as copying mechanism since it introduced lesser delay compared to other mechanisms such as pre-copy. However, the time delay and error rates are not proved to be satisfactory. While the implementation of the previous proposed solution still continued, hand-off solution came to our mind. Therefore, the state of the proposed hand-off solution is research and learn with no implementation.  



\section{Broad Impact}


\section{Ethical Considerations}

\chapter{PROJECT DEFINITION AND PLANNING}
\section{Project Definition}
\section{Project Planning}
\subsection{Project Time and Resource Estimation}
\subsection{Success Criteria}
\subsection{Risk Analysis}
\subsection{Team Work (if applicable)}

\chapter{RELATED WORK}
\section{COMIC-RAN: First Version [1]}

The COMIC-RAN project by Ömer Şükrü Uyduran had the same vision with our project. In fact, we have taken COMIC-RAN project over from Uyduran in order to make it more mature and complete. The project focused on the same problem as expected: Live migration of Cloud-RAN processes between different nodes. While the motivation behind the ideas was the same, the methodology used in Uyduran's implementation was quite different. Rather than using handover protocol between RRH units, Uyduran was working on a different migration technique: Containarization of processes. He implemented a specialized container application, Jailor, that was specific to the problem. Jailor was able to copy all states(memory pages) of a process that runs on a virtual machine(VM) to another VM. Post-copy was used for copying mechanism. It introduced a time delay that could not be tolerable in the project. Therefore, he and after him, Furkan and me have tried to come up with suitable ideas to mitigate the time problem as much as possible. However, there was always the possibility of non-stop modification of processes that were being copied. Since these processes were extremely time sensitive and very dynamically changing, copying mechanism had to be deterministically ensuring.

The idea proposed and implemented by Uyduran was also descendant of another one, Ahmet Buğra Taşdan and Salih Sevgican's 5G/CloudRAN project. Rather than using container based migration, they implemented a virtual machine based migration between physical machines. Similar to our case, this idea was also abandoned due to time delay issues. Even though the container-based solution of Uyduran solved the time problem of VM based solution, the time delay was never assured to be satisfying to our purpose.  


\section{5G/CloudRAN & Container Founded 5G vRAN Network [2]}

The idea proposed and implemented by Uyduran was also descendant of another one, Ahmet Buğra Taşdan and Salih Sevgican's 5G/CloudRAN project. Rather than using container based migration, they implemented a virtual machine based migration between physical machines. Similar to our case, this idea was also abandoned due to time delay issues. Another contribution that Taşdan and Sevgican's project provided was the use of Software Defined Networking(SDN) in order to manage traffic during the live migration process. 

After the implementation of VM-based live migration project, a new one that tried to solve the problem with container-based solution was proposed. Ömer Cihan Benzer and Yunus Emre Topal came up with the idea of utilizing current containerization tools to satisfy the time delay and resource allocation requirement. Main difference between VM-based solution and container-based solution could be clearly seen in this project, which also inspired Uyduran in the direction of implementing a special sand-box tool. 

These two projects and also the first version of COMIC-RAN have strong relations with each other. The idea started with 5G/CloudRAN project had been developed step by step to the current version of itself. Even though our idea of implementing the live migration of 5G processes differs from these three, they made the path clear for Cloud-RAN migration.


\section{COMIC-RAN [3]}


\chapter{METHODOLOGY}
Solution methods.

\chapter{REQUIREMENTS SPECIFICATION}
Use case diagrams.

\chapter{DESIGN}

\section{Information Structure}
ER Diagrams.

\section{Information Flow}
Activity diagrams, sequence diagrams, Business Process Modeling Notation.

\section{System Design}
Class diagrams, module diagrams.

\section{User Interface Design (if applicable)}

\chapter{IMPLEMENTATION AND TESTING}
\section{Implementation}
\section{Testing}
\section{Deployment}
Deployment diagram, building instructions, docker/kubernetes, readme, system manual and user manual

\chapter{RESULTS}

\chapter{CONCLUSION}

Citation examples: \cite{conference1}, \cite{article1}, \cite{book1}, \cite{mit}. Footnote example\footnote{More details: {\url{https://www.cmpe.boun.edu.tr/}}}. Referring to figures and tables: Figure \ref{fig:boun}. Table \ref{table:shortTable}.

\begin{figure}[h!]
\centering
\includegraphics[width=0.4\textwidth]{figures/bu-logo.png}
\caption{Figure caption}
\label{fig:boun}
\end{figure}

\begin{table}[thbp]
\vskip\baselineskip 
\caption[Sample table]{Table caption.}
\begin{center}
\begin{tabular}{|c|c|c|} \hline
 & \textbf{Header 1}& \textbf{Header 2}\\\hline
\textbf{Row 1} & 100  & 300 \\\hline
\textbf{Row 2} & 200  & 400 \\\hline
\end{tabular}
\label{table:shortTable}
\end{center}
\end{table}

\bibliographystyle{styles/fbe_tez_v11}
\bibliography{references}

\appendix	
\chapter{SAMPLE APPENDIX}
Contents of the appendix.

\end{document}
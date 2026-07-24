from abc import ABC, abstractmethod
import logging
import subprocess
from typing import List, Optional

from . import ids_batch as ids
from . response import CarisBatchResponse


Command = List[str]


class CarisBatchProcessAbstract(ABC):
    """
    Class permettant de construire et d'éxécuter des commands Caris Batch.
    """
    def __init__(self, environment) -> None:
        """
        Constructeur de la classe CarisBatchUtils.

        :param environment: Le chemin de l'instance de Caris Batch à utiliser.
        """
        self._caris_batch_environment = environment

    def make_command_line(
            self,
            process: Optional[str],
            options: Optional[List[str]] = None,
            source: Optional[List[str]] = None,
            destination: Optional[List[str]] = None,
            write_log: bool = False
    ) -> Command:
        """
        Méthode qui construit une ligne de commande Caris Batch.

        :param process: (str) Le nom du processus.
        :param options: (Optional[List[str]]) Les options du processus.
        :param source: (Optional[List[str]]) Les fichiers sources.
        :param destination: (Optional[List[str]]) La destination.
        :param write_log: (bool) True pour écrire dans le log de Caris, False sinon.

        :return: (Command) Une commande Caris Batch prête à être exécutée.
        """
        destination_list = destination or []
        source_list = source or []
        options = options or []
        run = [ids.RUN, process]
        log = [ids.WRITE_LOG] if write_log else []

        return [self._caris_batch_environment] + run + options + source_list + destination_list + log

    @abstractmethod
    def caris_batch_run(self, command: Command) -> CarisBatchResponse:
        """
        Méthode qui exécute une commande Caris Batch.

        :param command: (Command) La commande à exécuter.
        :return: (CarisBatchResponse) Un objet CarisBatchResponse.
        """


class CarisBatchProcess(CarisBatchProcessAbstract):
    def caris_batch_run(self, command: Command) -> CarisBatchResponse:
        """
        Méthode qui exécute une commande Caris Batch.

        :param command: (Command) La commande à exécuter.
        :return: (CarisBatchResponse) Un objet CarisBatchResponse.
        """
        process = subprocess.Popen(
            command,
            shell=True,  # todo à valider
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.PIPE
        )

        out, err = process.communicate()

        stdout = self._format_std(out)
        stderr = self._format_std(err)

        return CarisBatchResponse(stdout, stderr)

    @staticmethod
    def _format_std(std: bytes, codec: str = ids.LATIN) -> List[str]:
        """
        Méthode permettant de décoder un objet bytes et de retourner une liste de chaînes de caractères.

        :param std: (bytes) Un objet bytes représentant le stdout ou le stderr.
        :param codec: (str) L'encodage à utiliser.
        :return: (List[str]) Une liste de chaînes de caractères représentant le stdout ou le stderr.
        """
        std = std.decode(codec).split(ids.NEW_LINE)
        return [line for line in std if line != ids.EMPTY_STRING]


class CarisBatchProcessRT(CarisBatchProcessAbstract):
    def __init__(self, environment, logger: Optional[logging.Logger] = None) -> None:
        """
        Constructeur de la classe CarisBatchUtils.

        :param logger: (logging.Logger) Un logger.
        """
        super().__init__(environment)
        self._logger = logger or logging.getLogger(__name__)

    def caris_batch_run(self, command: Command) -> CarisBatchResponse:
        """
        Méthode qui exécute une commande Caris Batch.

        :param command: (Command) La commande à exécuter.
        :return: (CarisBatchResponse) Un objet CarisBatchResponse.
        """
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.PIPE
        )

        stdout = []
        stderr = []

        while True:
            output_stdout = process.stdout.readline()
            output_stderr = process.stderr.readline()

            if process.poll() is not None:
                break
            if output_stdout and output_stdout != ids.EMPTY_STRING:
                line = output_stdout.strip().decode()
                self._logger.info(line)
                stdout.append(line)
            if output_stderr and output_stderr != ids.EMPTY_STRING:
                line = output_stderr.strip().decode()
                self._logger.error(line)
                stderr.append(line)

        return CarisBatchResponse(stdout, stderr)

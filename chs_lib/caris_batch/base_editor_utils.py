import os
from typing import Union, List, Tuple

from . batch.batch_processor import CarisBatchProcessAbstract
from . exceptions_batch import BandError
from . batch.response import CarisBatchResponse


class BaseEditorUtils:
    """
    Classe permettant d'interagir avec les commandes Caris Bacth Utility de Base Editor.
    """

    def __init__(self, caris_batch_process: CarisBatchProcessAbstract) -> None:
        """
        Constructeur de la classe.

        :param caris_batch_process: (CarisBatchProcessAbstract) Un objet respectant l'interface
                                            de CarisBatchProcessAbstract.
        """
        self._batch_process = caris_batch_process

    def add_computed_band(
            self, file: str, band: str, expression: str = None, expression_file: str = None,
            axis: str = 'DOWN', computed_band_type: str = 'Elevation', args: List[str] = None
    ) -> CarisBatchResponse:
        """
        Méthode permettant de créer une nouvelle couche calculée à partir d'une expression.

        :param file: (str) Un fichier .csar.
        :param band: (str) Le nom de la couche à créer.
        :param expression: (str) Une expression pour le calcul de la nouvel couche.
        :param expression_file: (str) Un fichier texte contenant une expression. Si le paramètre expression est
                                        spécifié, le fichier est ignoré.
        :param axis: (str) Le sens de l'axe Z {DOWN ou UP}.
        :param computed_band_type: (str) Le type de données dans la couche {Elevation ou Numeric}.
        :param args: (List[str]) Une liste de paramètres additionnels à ajouter à la commande.
        :return: Un object CarisBatchResponse.
        :raise: FileNotFoundError lorsque le fichier .csar d'entrée est inexistant.
        """
        if not os.path.exists(file):
            raise FileNotFoundError('Fichier *.csar inexistant.')

        exp = []
        if expression is not None:
            exp = ['--expression', expression]
        elif expression_file is not None:
            exp = ['--expression-file', expression_file]

        args = args if args is not None else []

        command = self._batch_process.make_command_line(
            process='AddComputedBand',
            options=[
                        '--compute-band', band,
                        '--z-axis-convention', axis,
                        '--computed-band-type', computed_band_type
                    ] + exp + args,
            source=[file],
            destination=[]
        )

        response = self._batch_process.caris_batch_run(command)

        return response

    def create_soundings_from_coverage(
            self, file: str, output: str, radius: str = None, min_distance: list = None, band: str = 'Depth',
            bias: str = 'MAX', designated: bool = True, catalogue: str = 'Bathy DataBASE', scale: str = '1',
            args: List[str] = None
    ) -> CarisBatchResponse:
        """
        Méthode permettant de créer un fichier .csar qui représente une sous-sélection du fichier d'entrée.

        :param file: (str) Un fichier .csar.
        :param output: (str) Le chemin du fichier .csar de sortie.
        :param radius: (str) La valeur du rayon de la distance minimale entre les sondes ainsi
                                que son unité (m ou deg). Cet option outre-passe le paramètre min_distance.
        :param min_distance: (list(list[str])) --minimum-distance suivie des trois valeurs. Peut être répété.
                                           <Radius> - La distance minimale entre les sondes.
                                           <MinValue> - Valeur minimale de l'intervale.
                                           <MaxValue> - Valeur maximale de l'intervale.
                                Ce paramètre est ignoré si radius n'est pas None.
        :param scale: (str) La valeur de l'échelle à appliquer au paramètre radius. Valeur de 1 par défaut.
        :param band: (str) La couche du fichier avec laquelle effectuer la sélection.
        :param bias: (str) MIN, pour les valeurs minimales du voisinage,
                             MAX, pour les valeurs maximales du voisinage.
                             ALL, pour prendre l'ensemble des noeuds.
        :param designated: (bool) True pour appliquer les sondes désignées, False sinon.
        :param catalogue: (str) (str) Le catalogue à utiliser.
        :param args: (List[str]) Une liste de paramètres additionnels à ajouter à la commande.
        :return: Un object CarisBatchResponse.
        :raise: FileNotFoundError lorsque le fichier .csar d'entrée est inexistant.
        """
        # Avertissement : Le paramètre CARIS:NONE présente un bug et la
        # convention de l'axe des Z est 'up is positive' (BE5.4.8).
        if not os.path.exists(file):
            raise FileNotFoundError('Fichier *.csar inexistant.')

        minimum_distance = []
        if radius is not None:
            minimum_distance = ['--minimum-distance', radius, 'CARIS:NONE', 'CARIS:NONE']
        elif min_distance is None:
            minimum_distance = ['--minimum-distance', '10m', 'CARIS:NONE', 'CARIS:NONE']
        elif min_distance is not None:
            for distance in min_distance:
                minimum_distance = minimum_distance + ['--minimum-distance'] + distance

        apply_designated = []
        if designated:
            apply_designated = ['--apply-designated']

        args = args if args is not None else []

        command = self._batch_process.make_command_line(
            process='CreateSoundingsFromCoverage',
            options=[
                        '--input-band', band,
                        '--feature-catalogue', catalogue,
                        '--selection-bias', bias,
                        '--scale', scale
                    ] + apply_designated + min_distance + args,
            source=[file],
            destination=[output]
        )

        response = self._batch_process.caris_batch_run(command)

        return response

    def difference_coverage(
            self, file1: str, file2: str, output: str, band1: str = 'Depth', band2: str = 'Depth',
            args: List[str] = None
    ) -> CarisBatchResponse:
        """
        Méthode permettant de créer un fichier .csar correspondant à la différence entre 2 fichiers ou couches.

        :param file1: (str) Un fichier .csar.
        :param file2: (str) Un fichier .csar.
        :param output: (str) Le chemin du fichier de sortie.
        :param band1: (str) La couche du fichier avec laquelle effectuer l'opération.
        :param band2: (str) La couche du fichier avec laquelle effectuer l'opération.
        :param args: (List[str]) Une liste de paramètres additionnels à ajouter à la commande.
        :return: Un object CarisBatchResponse.
        :raise: FileNotFoundError lorsque le fichier .csar d'entrée est inexistant.
        """
        if not os.path.exists(file1) or not os.path.exists(file2):
            raise FileNotFoundError('Fichier *.csar inexistant.')

        args = args if args is not None else []

        command = self._batch_process.make_command_line(
            process='DifferenceCoverages',
            options=[
                '--difference-type', 'RASTER',
                '--input-band', band1,
                '--difference-file', file2,
                '--difference-band', band2
            ] + args,
            source=[file1],
            destination=[output]
        )
        response = self._batch_process.caris_batch_run(command)

        return response

    def export_coverage_to_ascii(
            self, file: str, output: str, include_band: List[Tuple[str, str]] = None,
            coordinate_format: str = 'LLDG_DMS', header: bool = True, args: List[str] = None
    ) -> CarisBatchResponse:
        """
        Méthode permettant d'exporter un fichier *.csar en fichier ASCII.

        :param file: (str) Un fichier .csar.
        :param output: (str) Le chemin du fichier de sortie en format *.txt.
        :param include_band: (list[Tuple[str, str]]) Un liste des chaînes de caractères comprenant le nom de
                                la couche sa présicion (nombre de décimal). ex: [('Depth', '5'), ('Shoal', '2)].
        :param coordinate_format: (str) Le format des coordonnées pour le fichier de sortie.
                                            •GROUND: Ground
                                            •LLDG_DMS: Geographic DMS
                                            •LLDG_DMS_NO_FORMAT: Geographic DMS (no formatting)
                                            •LLDG_DM: Geographic DM
                                            •LLDG_DD: Geographic DD
        :param header: (bool) True pour inclure une entête, False sinon.
        :param args: (List[str]) Une liste de paramètres additionnels à ajouter à la commande.
        :return: Un object CarisBatchResponse.
        :raise: FileNotFoundError lorsque le fichier .csar d'entrée est inexistant.
        """
        if not os.path.exists(file):
            raise FileNotFoundError('Fichier *.csar inexistant.')

        include_bands = []
        if include_band is None:
            include_bands = ['--include-band', 'ALL', '3']
        else:
            for band in include_band:
                include_bands += ["--include-band"] + [band[0], band[1]]

        inlude_header = []
        if header:
            inlude_header = ['--include-header']

        args = args if args is not None else []

        command = self._batch_process.make_command_line(
            process='ExportCoverageToASCII',
            options=[
                        '--coordinate-format', coordinate_format
                    ] + include_bands + inlude_header + args,
            source=[file],
            destination=[output]
        )

        response = self._batch_process.caris_batch_run(command)

        return response

    def export_csar_to_raster(
            self, file: str, output: str, file_type: str = 'GEOTIFF', include_band: str = 'Depth',
            args: List[str] = None
    ) -> CarisBatchResponse:
        """
        Méthode permettant d'exporter un fichier .csar dans un autre format raster.

        :param file: (str) Un fichier .csar.
        :param output: (str) Le chemin du fichier de sortie.
        :param file_type: (str) Le format du fichier de sortie.
        :param include_band: (str) La ou les couches à inclure.
        :param args: (List[str]) Une liste de paramètres additionnels à ajouter à la commande.
        :return: Un object CarisBatchResponse.
        :raise: FileNotFoundError lorsque le fichier .csar d'entrée est inexistant.
        """
        if not os.path.exists(file):
            raise FileNotFoundError('Fichier *.csar inexistant.')

        args = args if args is not None else []

        command = self._batch_process.make_command_line(
            process='ExportRaster',
            options=[
                '--output-format', file_type,
                '--include-band', include_band
            ] + args,
            source=[file],
            destination=[output]
        )

        response = self._batch_process.caris_batch_run(command)

        if not response.is_ok:
            if response.stderr[0].startswith('ERROR: The specified band name'):
                raise BandError("La couche '{}' n'existe pas dans ce fichier.".format(include_band))

        return response

    def export_hob_to_shp(
            self, file: str, output: str, catalogue: str = 'Bathy DataBASE', args: List[str] = None
    ) -> CarisBatchResponse:
        """
        Méthode permettant d'exporter un fichier .hob en type .shp.

        :param file: (str) Un fichier .hob.
        :param output: (str) Le chemin du fichier .shp de sortie.
        :param catalogue: (str) Le catalogue à utiliser.
        :param args: (List[str]) Une liste de paramètres additionnels à ajouter à la commande.
        :return: Un object CarisBatchResponse.
        :raise: FileNotFoundError lorsque le fichier .csar d'entrée est inexistant.
        """
        if not os.path.exists(file):
            raise FileNotFoundError('Fichier *.hob inexistant.')

        args = args if args is not None else []

        command = self._batch_process.make_command_line(
            process='ExportFeaturesToShapefile',
            options=[
                '--feature-catalogue', catalogue
            ] + args,
            source=[file],
            destination=[output]
        )

        response = self._batch_process.caris_batch_run(command)

        return response

    def export_hob_to_wkt(
            self, file: str, output: str, catalogue: str = 'Bathy DataBASE', args: List[str] = None
    ) -> CarisBatchResponse:
        """
        Méthode permettant d'exporter un fichier .hob en type .wkt.

        :param file: (str) Un fichier .hob.
        :param output: (str) Le chemin du fichier .wkt de sortie.
        :param catalogue: (str) Le catalogue à utiliser.
        :param args: (List[str]) Une liste de paramètres additionnels à ajouter à la commande.
        :return: Un object CarisBatchResponse.
        :raise: FileNotFoundError lorsque le fichier .csar d'entrée est inexistant.
        """
        if not os.path.exists(file):
            raise FileNotFoundError('Fichier *.hob inexistant.')

        args = args if args is not None else []

        command = self._batch_process.make_command_line(
            process='ExportTOWkt',
            options=[
                '--feature-catalogue', catalogue
            ] + args,
            source=[file],
            destination=[output]
        )

        response = self._batch_process.caris_batch_run(command)

        return response

    def extract_coverage(
            self, file: str, output: str, extract_type: str = 'INCLUSIVE', include_band: list = None,
            geometry: Union[list, str] = None, args: List[str] = None
    ) -> CarisBatchResponse:
        """
        Méthode permettant de couper un fichier .csar avec une geométrie en format WKT.

        :param file: (str) Un fichier .csar.
        :param output: (str) Le chemin du fichier .csar de sortie.
        :param extract_type: (str) INCLUSIVE, pour les données à l'intérieure de la geométrie,
                                     EXLCUSIVE, pour les données à l'extérieure de la geométrie.
        :param include_band: (list) La ou les couches à inclure.
        :param geometry: (Union[list, str]) Une liste de 2 éléments, une chaine de caractère représeantant
                            la géométrie WKT et une chaîne de caractère représentant le CRS de la géométrie, ou
                            Le chemin d'un fichier WKT contenant la geométrie et le CRS.
        :param args: (List[str]) Une liste de paramètres additionnels à ajouter à la commande.
        :return: Un object CarisBatchResponse.
        :raise: FileNotFoundError lorsque le fichier .csar d'entrée est inexistant.
        """
        if not os.path.exists(file):
            raise FileNotFoundError('Fichier *.csar inexistant.')

        include_bands = []
        if include_band is None:
            include_bands = ['--include-band', 'ALL']
        else:
            for band in include_band:
                include_bands = include_bands + ['--include-band'] + [band]

        if isinstance(geometry, str):
            if not os.path.exists(geometry):
                raise FileNotFoundError('Fichier *.wkt inexistant.')
            geom = ['--geometry-file', geometry]
        elif isinstance(geometry, list):
            geom = ['--geometry'] + geometry
        else:
            raise ValueError("Le paramètre 'geometry' est obligatoire.")

        args = args if args is not None else []

        command = self._batch_process.make_command_line(
            process='ExtractCoverage',
            options=[
                        '--extract-type', extract_type
                    ] + include_bands + geom + args,
            source=[file],
            destination=[output]
        )

        response = self._batch_process.caris_batch_run(command)

        return response

    def fill_raster_holidays(
            self, file: str, output: str, band: str = 'Depth', matrix: str = '5x5',
            include_band: str = 'ALL', neighbours: str = '6', args: List[str] = None
    ) -> CarisBatchResponse:
        """
        Méthode permettant de populer les cellules vides en fonction de son voisinage.

        :param file: (str) Un fichier .csar.
        :param output: (str) Le chemin du fichier .csar de sortie.
        :param band: (str) La couche du fichier avec laquelle effectuer l'opération.
        :param matrix: (str) Les dimensions de la matrice à utiliser. {3x3 ou 5x5}
        :param include_band: (str) La ou les couches à inclure.
        :param neighbours: (str) Le nombre minimal de voisins à inclure dans le calcul.
        :param args: (List[str]) Une liste de paramètres additionnels à ajouter à la commande.
        :return: Un object CarisBatchResponse.
        :raise: FileNotFoundError lorsque le fichier .csar d'entrée est inexistant.
        """
        if not os.path.exists(file):
            raise FileNotFoundError('Fichier *.csar inexistant.')

        args = args if args is not None else []

        command = self._batch_process.make_command_line(
            process='FillRasterHolidays',
            options=[
                '--input-band', band,
                '--matrix', matrix, neighbours,
                '--include-band', include_band
            ] + args,
            source=[file],
            destination=[output]
        )

        response = self._batch_process.caris_batch_run(command)

        return response

    def filter_coverage(
            self, file: str, output: str, expression: str, include_band: str = 'ALL', args: List[str] = None
    ) -> CarisBatchResponse:
        """
        Méthode permettant de filtrer une couche à partir d'une expression.

        :param file: (str) Un fichier .csar.
        :param output: (str) Le chemin du fichier .csar de sortie.
        :param expression: (str) Une expression pour le filtrage de la couche. Note: l'axe Z est positif vers le haut.
        :param include_band: (str) La ou les couches à inclure. --include-band Peut être répété.
        :param args: (List[str]) Une liste de paramètres additionnels à ajouter à la commande.
        :return: Un object CarisBatchResponse.
        :raise: FileNotFoundError lorsque le fichier .csar d'entrée est inexistant.
        """
        if not os.path.exists(file):
            raise FileNotFoundError('Fichier *.csar inexistant.')

        args = args if args is not None else []

        command = self._batch_process.make_command_line(
            process='FilterCoverage',
            options=[
                '--include-band', include_band,
                '--expression', expression
            ] + args,
            source=[file],
            destination=[output]
        )

        response = self._batch_process.caris_batch_run(command)

        return response

    def finalize_raster(
            self, file: str, output: str, include_band: list = None, designated: bool = True,
            uncertainty: str = 'GREATER', args: List[str] = None
    ) -> CarisBatchResponse:
        """
        Méthode permettant de finaliser les surfaces, défénir la source d'incertitude et d'appliquer
        les sondes désignées.

        :param file: (str) Un fichier .csar.
        :param output: (str) Le chemin du fichier .csar de sortie.
        :param designated: (bool) True, pour appliquer la valeur des sondes désignés à la couche
                                d'élévation primaire, False sinon.
        :param include_band: list[(str)] La ou les couches à inclure. --include-band Peut être répété.
        :param uncertainty: (str) La source de l'incertitude à inclure dans la surface
                                finalisée [GREATER, UNCERT, STD_DEV].
        :param args: (List[str]) Une liste de paramètres additionnels à ajouter à la commande.
        :return: Un object CarisBatchResponse.
        :raise: FileNotFoundError lorsque le fichier .csar d'entrée est inexistant.
        """
        if not os.path.exists(file):
            raise FileNotFoundError('Fichier *.csar inexistant.')

        include_bands = []
        if include_band is None:
            include_bands = ['--include-band', 'ALL']
        else:
            for band in include_band:
                include_bands = include_bands + ['--include-band'] + [band]

        apply_designated = []
        if designated:
            apply_designated = ['--apply-designated']

        args = args if args is not None else []

        command = self._batch_process.make_command_line(
            process='FinalizeRaster',
            options=[
                        '--uncertainty-source', uncertainty
                    ] + include_bands + apply_designated + args,
            source=[file],
            destination=[output]
        )

        response = self._batch_process.caris_batch_run(command)

        return response

    def import_to_csar(
            self, file: str, output: str, file_format: str, output_resolution: str,
            include_band: List[str] = None, primary_band: str = 'Depth', gridding_method: str = 'SHOAL',
            args: List[str] = None
    ) -> CarisBatchResponse:
        """
        Méthode permettant de créer un fichier .csar.
        :param file: (str) Un fichier .csar.
        :param output: (str) Le chemin du fichier .csar de sortie.
        :param primary_band: (str) Bande principale du fichier resultant.
        :param file_format: (str) {ASCII, CRS, CSAR, C_AND_C, GSF, HOB, HTF, HYD93, LAS, NTX, RDP}
        :param include_band: (str) Nom de la bande supplémentaire à integrer.
        :param gridding_method: (str) Méthode pour définir les valeurs.
                            BASIC, TPU, SHOAL, SHOAL_TRUE, DEEP_TRUE, DISTANCE_PLANE, FARTHEST, FARTHEST_ABOVE.
        :param output_resolution: (str) La résolution du fichier output (ex: 0.001deg).
        :param args: (List[str]) Une liste de paramètres additionnels à ajouter à la commande.
        :return: Un object CarisBatchResponse.
        :raise: FileNotFoundError lorsque le fichier .csar d'entrée est inexistant.
        """

        if not os.path.exists(file):
            raise FileNotFoundError('Fichier *.csar inexistant.')

        include_bands = []
        if include_band is None:
            include_bands = ['--include-band', 'ALL']
        else:
            for band in include_band:
                include_bands = include_bands + ['--include-band'] + [band]

        args = args if args is not None else []

        command = self._batch_process.make_command_line(
            process='ImportPoints',
            options=[
                        '--input-format', file_format,
                        '--primary-band', primary_band,
                        '--gridding-method', gridding_method,
                        '--resolution', output_resolution
                    ] + include_bands + args,
            source=[file],
            destination=[output]
        )

        response = self._batch_process.caris_batch_run(command)

        return response

    def resample_surface_raster(
            self, file: str, output: str, resolution: str, args: List[str] = None
    ) -> CarisBatchResponse:
        """
        Méthode permettant de rééchantillonner un fichier .csar.

        :param file: (str) Un fichier .csar.
        :param output: (str) Le chemin du fichier .csar de sortie.
        :param resolution: (str) La résolution du fichier et son unité (m, deg, ...).
        :param args: (List[str]) Une liste de paramètres additionnels à ajouter à la commande.
        :return: Un object CarisBatchResponse.
        :raise: FileNotFoundError lorsque le fichier .csar d'entrée est inexistant.
        """
        if not os.path.exists(file):
            raise FileNotFoundError('Fichier *.csar inexistant.')

        args = args if args is not None else []

        command = self._batch_process.make_command_line(
            process='ResampleSurfaceToRaster',
            options=[
                '--resolution', resolution
            ] + args,
            source=[file],
            destination=[output]
        )

        response = self._batch_process.caris_batch_run(command)

        return response

    def shift_elevation_band(
            self, file: str, output: str, band: str = 'Depth', include_band: str = 'ALL',
            shift_type: str = 'RASTER', output_vertical_crs: str = 'PACD', shift_file: str = None,
            shift_value: str = None, elevation_band: str = 'Depth', args: List[str] = None
    ) -> CarisBatchResponse:
        """
        Méthode permettant de modifier les valeurs d'une couche d'élévation.

        :param file: (str) Un fichier .csar.
        :param output: (str) Le chemin du fichier .csar de sortie.
        :param band: (str) La couche du fichier avec laquelle effectuer le shift.
        :param include_band: (str) La ou les couches à inclure.
        :param shift_type: (str) {ASCII, VALUE, RASTER}.
        :param output_vertical_crs: (str) Le système de référence verticale.
        :param shift_file: (str) Le fichier a utilisé pour le shift.
        :param shift_value: (str) La valeur à appliquer pour le shift.
        :param elevation_band: (str) La bande à utiliser pour le fichier de raster de shift.
        :param args: (List[str]) Une liste de paramètres additionnels à ajouter à la commande.
        :return: Un object CarisBatchResponse.
        :raise: FileNotFoundError lorsque le fichier .csar d'entrée est inexistant.
        """
        if not os.path.exists(file):
            raise FileNotFoundError('Fichier *.csar inexistant.')

        opts_type = []
        if shift_type == 'VALUE':
            opts_type = ['--shift-value', shift_value]
        elif shift_type == 'ASCII':
            opts_type = ['--shift-file', shift_file]
        elif shift_type == 'RASTER':
            opts_type = ['--shift-file', shift_file, '--elevation-band', elevation_band]

        args = args if args is not None else []

        command = self._batch_process.make_command_line(
            process='ShiftElevationBands',
            options=[
                        '--input-band', band,
                        '--include-band', include_band,
                        '--output-vertical-crs', output_vertical_crs,
                        '--shift-type', shift_type
                    ] + opts_type + args,
            source=[file],
            destination=[output]
        )

        response = self._batch_process.caris_batch_run(command)

        return response

    def thin_points(
            self, file: str, output: str, radius: str = None, min_distance: list = None,
            band: str = 'Depth', bias: str = 'MAX', designated: list = None, include_band: str = 'ALL',
            scale: str = '1', args: List[str] = None
    ) -> CarisBatchResponse:
        """
        Méthode permettant de créer un fichier .csar qui représente une sous-sélection du fichier d'entrée.

        :param file: (str) Un fichier .csar.
        :param output: (str) Le chemin du fichier .csar de sortie.
        :param radius: (str) La valeur du rayon de la distance minimale entre les sondes ainsi
                                que son unité (m ou deg). Cet option outre-passe le paramètre min_distance.
        :param scale: (str) La valeur de l'échelle à appliquer au paramètre radius. Valeur de 1 par défaut.
        :param min_distance: (list(list[str])) --minimum-distance suivie des trois valeurs. Peut être répété.
                                           <Radius> - La distance minimale entre les sondes.
                                           <MinValue> - Valeur minimale de l'intervale.
                                           <MaxValue> - Valeur maximale de l'intervale.
                                Ce paramètre est ignoré si radius n'est pas None.
        :param band: (str) La couche du fichier avec laquelle effectuer la sélection.
        :param bias: (str) MIN, pour les valeurs minimales du voisinage,
                             MAX, pour les valeurs maximales du voisinage.
        :param designated: (list[str]) '--apply-designated' avec une ou plusieurs options parmi
                                                                  <MultipleDesignated> [KEEP_ALL ou THIN],
                                                                  <BiasRelevance> [APPLY_BIAS ou OVERRIDE_BIAS]
        :param include_band: (str) La ou les couches à inclure.
        :param args: (List[str]) Une liste de paramètres additionnels à ajouter à la commande.
        :return: Un object CarisBatchResponse.
        :raise: FileNotFoundError lorsque le fichier .csar d'entrée est inexistant.
        """
        # Avertissement : Le paramètre CARIS:NONE présente un bug et la
        # convention de l'axe des Z est 'up is positive' (BE5.4.8).
        if not os.path.exists(file):
            raise FileNotFoundError('Fichier *.csar inexistant.')

        minimum_distance = []
        if radius is not None:
            minimum_distance = ['--minimum-distance', radius, 'CARIS:NONE', 'CARIS:NONE']
        elif min_distance is None:
            minimum_distance = ['--minimum-distance', '10m', 'CARIS:NONE', 'CARIS:NONE']
        elif min_distance is not None:
            for distance in min_distance:
                minimum_distance = minimum_distance + ['--minimum-distance'] + distance

        if designated is None:
            designated = ['--apply-designated', 'KEEP_ALL', 'APPLY_BIAS']

        args = args if args is not None else []

        command = self._batch_process.make_command_line(
            process='ThinPoints',
            options=[
                        '--method', 'APPLY_BIAS',
                        '--include-band', include_band,
                        '--scale', scale,
                        '--input-band', band,
                        '--bias', bias,
                    ] + designated + minimum_distance + args,
            source=[file],
            destination=[output]
        )

        response = self._batch_process.caris_batch_run(command)

        return response

    def validate_coverage(self, file: str, args: List[str] = None) -> CarisBatchResponse:
        """
        Méthode permettant de vectoriser un fichier .csar.

        :param file: (str) Un fichier .csar.
        :param args: (List[str]) Une liste de paramètres additionnels à ajouter à la commande.
        :return: Un object CarisBatchResponse.
        :raise: FileNotFoundError lorsque le fichier .csar d'entrée est inexistant.
        """
        if not os.path.exists(file):
            raise FileNotFoundError('Fichier *.csar inexistant.')

        args = args if args is not None else []

        command = self._batch_process.make_command_line(
            process='ValidateCoverage',
            options=[] + args,
            source=[file]
        )

        response = self._batch_process.caris_batch_run(command)

        return response

    def vectorize_raster(
            self, file: str, output: str, band: str = 'Depth', catalogue: str = 'Bathy DataBASE',
            feature: str = 'cvrage', args: List[str] = None
    ) -> CarisBatchResponse:
        """
        Méthode permettant de vectoriser un fichier .csar.

        :param file: (str) Un fichier .csar.
        :param output: (str) Le chemin du fichier .hob de sortie.
        :param band: (str) a couche du fichier avec laquelle effectuer la vectorisation.
        :param catalogue: (str) Le catalogue à utiliser.
        :param feature: (str) Le feature à utiliser.
        :param args: (List[str]) Une liste de paramètres additionnels à ajouter à la commande.
        :return: Un object CarisBatchResponse.
        :raise: FileNotFoundError lorsque le fichier .csar d'entrée est inexistant.
        """
        if not os.path.exists(file):
            raise FileNotFoundError('Fichier *.csar inexistant.')

        args = args if args is not None else []

        command = self._batch_process.make_command_line(
            process='VectorizeRaster',
            options=[
                '--feature-catalogue', catalogue,
                '--polygon-feature', feature,
                '--input-band', band
            ] + args,
            source=[file],
            destination=[output]
        )

        response = self._batch_process.caris_batch_run(command)

        return response

    def server_combine_to_raster(
            self, output: str, database: str, host: str, username: str, password: str, rule_file: str,
            contributor_attribute: List[str], extent: List[str], output_crs: str, file: Union[List[str], str],
            output_vertical_crs: str = None, stats: bool = False, override_ambiguity: bool = True,
            use_cell_centres: bool = False, resolution: str = '1m', band: str = 'Depth',
            anchor: List[str] = None, footprint: str = None, args: List[str] = None
    ) -> CarisBatchResponse:
        """
        Méthode permettant de créer un combine à partir de la base de données.

        :param output: (str) Le chemin du fichier .csar de sortie ou l'URI.
        :param database: (str) Le nom de la base de données.
        :param host: (str) L'adresse du node de la base de données.
        :param username: (str) Le nom d'utilisateur.
        :param password: (str) Le mot de passe de l'utilisateur.
        :param rule_file: (str) Le chemin du fichier de règles à utiliser.
        :param contributor_attribute: list[str] Les attributs à inclure dans le combine.
        :param extent: list[str] L'étendue du combine en géographique <LowerX> - lower left X origin,
                                                                        <LowerY> - lower left Y origin,
                                                                        <UpperX> - upper right X origin,
                                                                        <UpperY> - upper right Y origin.
        :param output_crs: (str) Le epsg du crs (ex : EPSG:32188).
        :param file: Union(list[str], str) La liste des BOID des fichiers à inclure dans le combine ou un
                        fichier xml (create_source_xml_file).
        :param output_vertical_crs: (str) Le nom du crs verticale.
        :param stats: (bool) True pour recalculer les couches Density, Mean, Standard Deviation, Shoal
                                et Deep. False sinon.
        :param override_ambiguity: (str) True pour sélectionner la première valeur répondant aux critères des règles
                                            lors d'un conflit. False sinon.
        :param use_cell_centres: (str) True pour utiliser le centre de la cellule pour la position de la sonde.
        :param resolution: (str) La résolution du combine et son unité (m, deg, ...).
        :param band: (str) Le nom de la couche d'élévation.
        :param anchor: (str) HALF_RES est utilisé pour calculer une position de coordonnées pour un centre de cellule
                                qui est décalé de la moitié de la résolution (--anchor HALF_RES HALF_RES).
        :param footprint: (str) Une chaîne de caractères spécifiant la méthode à utiliser pour calculer les valeurs
                                    d'empreinte entre les pixels. {BILINEAR, BILINEAR_KEEP_HOLES, BICUBIC,
                                    BICUBIC_KEEP_HOLES, NEAREST_NEIGHBOUR}.
        :param args: (List[str]) Une liste de paramètres additionnels à ajouter à la commande.
        :return: Un object CarisBatchResponse.
        :raise: ValueError lorsque le paramètre file est invalide.
        """
        login = '{}/{}@{}'.format(username, password, host)

        vcrs = []
        if output_vertical_crs is not None:
            vcrs = ['--output-vertical-crs', output_vertical_crs]

        recompute_stat = []
        if stats:
            recompute_stat = ['--recompute-stats']

        override = []
        if override_ambiguity:
            override = ['--override-ambiguity']

        cell_centres = []
        if use_cell_centres:
            cell_centres = ['--use-cell-centres']

        contributor_attributes = []
        for attribute in contributor_attribute:
            contributor_attributes = contributor_attributes + ['--contributor-attribute'] + [attribute]

        extent = ['--extent'] + extent

        anchor = []
        if anchor is not None:
            anchor = ['--anchor'] + anchor

        footprint_type = []
        if footprint is not None:
            footprint_type = ['--footprint-type'] + [footprint]

        input_list = []
        if isinstance(file, str):
            if file.endswith('.xml'):
                input_list = [file]
        elif isinstance(file, list):
            input_list = file
        if not input_list:
            raise ValueError('Un fichier xml valide ou une liste de fichiers pour le combine est obligatoire.')

        args = args if args is not None else []

        command = self._batch_process.make_command_line(
            process='ServerCombineToRaster',
            options=[
                        '--database-name', database,
                        '--login', login,
                        '--rule-file', rule_file,
                        '--resolution', resolution,
                        '--primary-band', band,
                        '--output-crs', output_crs,
                        '--write-process-log'
                    ] + vcrs + recompute_stat + override + cell_centres + anchor + footprint_type +
                    extent + contributor_attributes + input_list + args,
            source=[],
            destination=[output]
        )

        response = self._batch_process.caris_batch_run(command)

        return response

    def warp(
            self, file: str, output: str, resolution: str, output_crs: str, primary_band: Tuple[str],
            input_bands: List[Tuple[str]] = None, output_vertical_crs: str = None, args: List[str] = None
    ) -> CarisBatchResponse:
        """
        Méthode permettant de faire un warp à un fichier .csar.

        :param file: (str) Un fichier .csar.
        :param output: (str) Le chemin du fichier .csar de sortie.
        :param resolution: (str) La résolution du combine et son unité (m, deg, ...). Exemple: 1m.
        :param output_crs: (str) Le epsg du crs (ex : EPSG:32188).
        :param primary_band: (str) Le nom de la couche d'élévation, la méthode d'interpolation et la méthode
                                        d'échantillonnage.
                                <Interpolation> - {BICUBIC, BICUBIC_KEEP_HOLE, BILINEAR, BILINEAR_KEEP_HOLE,
                                                   NEAREST_NEIGHBOUR, NONE}
                                <Sampling> - {MIN, MAX, NONE}
                            Exemple: Depth BILINEAR MIN
        :param input_bands: (list[tuple[str]]) Le nom des couches, leur méthode d'interpolation et leur
                                              méthode d'échantillonnage.
                                <Interpolation> - {BICUBIC, BICUBIC_KEEP_HOLE, BILINEAR, BILINEAR_KEEP_HOLE,
                                                   NEAREST_NEIGHBOUR, NONE}
                                <Sampling> - {FOLLOW_PRIMAR, NONE}
                            Exemple: Depth BILINEAR MIN
        :param output_vertical_crs: (str) Le nom du crs verticale.
        :param args: (List[str]) Une liste de paramètres additionnels à ajouter à la commande.
        :return: Un object CarisBatchResponse.
        :raise: FileNotFoundError lorsque le fichier .csar d'entrée est inexistant.
        """
        if not os.path.exists(file):
            raise FileNotFoundError('Fichier *.csar inexistant.')

        vcrs = []
        if output_vertical_crs is not None:
            vcrs = ['--output-vertical-crs', output_vertical_crs]

        primary_band = ['--primary-band'] + [primary_band[0], primary_band[1], primary_band[2]]

        bands = []
        if input_bands is not None:
            for band in input_bands:
                bands += ["--input-band"] + [band[0], band[1], band[2]]

        args = args if args is not None else []

        command = self._batch_process.make_command_line(
            process='WarpRaster',
            options=[
                        '--resolution', resolution,
                        '--output-crs', output_crs,
                    ] + vcrs + primary_band + bands + args,
            source=[file],
            destination=[output]
        )

        response = self._batch_process.caris_batch_run(command)

        return response

# if __name__ == "__main__":
#     coverage = r'D:\HDCS_Data\Originals_MHG\1300412.csar'
#     coverage_out = r'D:\HDCS_Data\Originals_MHG\test.csar'
#     wkt = r'D:\HDCS_Data\Originals_MHG\9000423_2020GardnerCanal_2m_EXTRACT.wkt'
#     # out = r'D:\HDCS_Data\BDBTestQC\sup.csar'
#     # hob = r'D:\HDCS_Data\BDBTestQC'
#     xml = r'D:\HDCS_Data\BDBTest\combine.xml'
#
#     from chs_utils.logger_utils import create_logger
#     from batch_utils import CarisBatchProcess, CarisBatchProcessRT
#
#     logger = create_logger('Batch', 'test', 'blue')
#
#     cbp = CarisBatchProcessRT(
#         environment=r'C:\Program Files\CARIS\BASE Editor\5.5\bin\carisbatch.exe',
#         logger=logger
#     )
#
#     beu = BaseEditorUtils(caris_batch_process=cbp)
#
#     response = beu.extract_coverage(coverage, coverage_out, geometry=wkt, extract_type='INCLUSIVE')
#
#     # response = beu.resample_surface_raster(file=coverage, output=coverage_out, resolution='50m')
#
#     # response = beu.validate_coverage(
#     #     r'C:\Users\bilodeauy\Desktop\recep\_Surfaces 2021 - ACharger\21e082117261_final.csar')
#
#     # feature_list = [
#     #     '3328d6c4-7150-11e6-801f-9457a56b97f0',
#     #     '3936c60a-f7e2-11e8-8000-9457a56b97f0',
#     #     '331a88b2-7150-11e6-8009-9457a56b97f0'
#     # ]
#
#     # write_xml_filter_file(create_bbox_valta_xml_filter(
#     #     lower_corner_lat=46.25,
#     #     lower_corner_lon=-72.25,
#     #     upper_corner_lat=46.5,
#     #     upper_corner_lon=-72,
#     #     valsta=[1, 6]
#     # ), xml)
#
#     # response = beu.server_combine_to_raster(
#     #     r'D:\Port_MTL\Combine_chenal\combine.csar',
#     #     'bdb_que_rest',
#     #     '142.130.48.49',
#     #     'bilodeauy',
#     #     'bilodeauy',
#     #     r'D:\Port_MTL\Combine_chenal\combine_rule.crfx',
#     #     ['BOID', 'OBJNAM', 'SUREND', 'CATZOC'],
#     #     # ['-72.25', '46.25', '-72', '46.5'],
#     #     ['-71.1984306', '46.7700167', '-70.2071654', '47.4563235'],
#     #     'EPSG:4326',
#     #     # ['222854.09', '5171349.34', '223151.95', '5171580.59'],
#     #     # 'EPSG:32187',
#     #     # feature_list,
#     #     r'D:\Port_MTL\Combine_chenal\selection.xml',
#     #     resolution='0.00001deg'
#     # )
#
#     # response = beu.export_coverage_to_ascii(
#     #     coverage,
#     #     coverage_out,
#     #     include_band=[('Depth', '4'), ('Shoal', '1')],
#     #     header=True,
#     #     coordinate_format='LLDG_DD'
#     # )
#
#     # response = beu.export_csar_to_raster(
#     #     file=coverage,
#     #     output=r'D:\HDCS_Data\BDBTest\combine.bag',
#     #     type='BAG',
#     #     args=[
#     #         '--uncertainty-type', 'UNKNOWN',
#     #         '--abstract', 'CHS',
#     #         '--status', 'COMPLETED',
#     #         '--party-role', 'OWNER',
#     #         '--legal-constraints', 'LICENSE',
#     #         '--security-constraints', 'RESTRICTED',
#     #         '--notes', 'CHS Non-navigational Bathymetric Data',
#     #         '--vertical-datum', 'ChartDatum'
#     #     ]
#     # )
#
#     # response = beu.export_csar_to_raster(
#     #     file=coverage,
#     #     output=r'C:\HDCS_Data\22c549110291\007-Surfaces\22c549110291_5m.tiff',
#     #     args=['--compression', 'LZW']
#     # )
#     #
#     # print(response)
#     print(response.is_ok)
#     print('fin')

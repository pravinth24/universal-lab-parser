"""Async batch processing for high-performance file parsing."""

import asyncio
from pathlib import Path
from typing import List, Dict, Optional, Callable
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
import glob

from universal_lab_parser import parse_file
from universal_lab_parser.core.data_model import LabData
from universal_lab_parser.utils.logger import get_logger

logger = get_logger(__name__)


class BatchProcessor:
    """High-performance batch processing of lab instrument files."""

    def __init__(
        self,
        max_workers: int = 4,
        use_processes: bool = False,
        fail_fast: bool = False,
    ):
        """
        Initialize batch processor.

        Args:
            max_workers: Number of parallel workers
            use_processes: Use multiprocessing instead of threading
            fail_fast: Stop on first error
        """
        self.max_workers = max_workers
        self.use_processes = use_processes
        self.fail_fast = fail_fast

    async def process_files_async(
        self,
        filepaths: List[Path],
        output_dir: Optional[Path] = None,
        output_format: str = "csv",
        progress_callback: Optional[Callable] = None,
    ) -> Dict[str, any]:
        """
        Process files asynchronously.

        Args:
            filepaths: List of file paths to process
            output_dir: Output directory for parsed files
            output_format: Output format (csv, json, parquet)
            progress_callback: Optional callback for progress updates

        Returns:
            Dictionary with processing results
        """
        logger.info(f"Starting batch processing of {len(filepaths)} files")

        results = {
            "success": [],
            "errors": [],
            "total": len(filepaths),
        }

        if output_dir:
            output_dir.mkdir(parents=True, exist_ok=True)

        # Create executor
        executor_class = ProcessPoolExecutor if self.use_processes else ThreadPoolExecutor

        with executor_class(max_workers=self.max_workers) as executor:
            loop = asyncio.get_event_loop()

            # Submit all tasks
            tasks = []
            for filepath in filepaths:
                task = loop.run_in_executor(
                    executor,
                    self._process_single_file,
                    filepath,
                    output_dir,
                    output_format,
                )
                tasks.append((filepath, task))

            # Process results as they complete
            for filepath, task in tasks:
                try:
                    result = await task

                    if result["success"]:
                        results["success"].append(result)
                        logger.debug(f"Successfully parsed: {filepath}")
                    else:
                        results["errors"].append(result)
                        logger.warning(f"Failed to parse: {filepath} - {result['error']}")

                        if self.fail_fast:
                            logger.error("Stopping due to fail_fast mode")
                            break

                    # Call progress callback
                    if progress_callback:
                        progress_callback(len(results["success"]) + len(results["errors"]), len(filepaths))

                except Exception as e:
                    logger.exception(f"Unexpected error processing {filepath}")
                    results["errors"].append({
                        "filepath": str(filepath),
                        "success": False,
                        "error": str(e),
                    })

        logger.info(
            f"Batch processing complete: "
            f"{len(results['success'])} success, {len(results['errors'])} errors"
        )

        return results

    def process_files(
        self,
        filepaths: List[Path],
        output_dir: Optional[Path] = None,
        output_format: str = "csv",
        progress_callback: Optional[Callable] = None,
    ) -> Dict[str, any]:
        """
        Synchronous wrapper for async batch processing.

        Args:
            filepaths: List of file paths
            output_dir: Output directory
            output_format: Output format
            progress_callback: Progress callback

        Returns:
            Processing results
        """
        return asyncio.run(
            self.process_files_async(
                filepaths,
                output_dir,
                output_format,
                progress_callback,
            )
        )

    @staticmethod
    def _process_single_file(
        filepath: Path,
        output_dir: Optional[Path],
        output_format: str,
    ) -> Dict[str, any]:
        """
        Process a single file (called by executor).

        Args:
            filepath: File to process
            output_dir: Output directory
            output_format: Output format

        Returns:
            Result dictionary
        """
        try:
            # Parse file
            data = parse_file(str(filepath))

            # Export if output_dir specified
            if output_dir:
                output_path = output_dir / f"{Path(filepath).stem}.{output_format}"

                if output_format == "csv":
                    data.to_csv(str(output_path))
                elif output_format == "json":
                    data.to_json(str(output_path))
                elif output_format == "parquet":
                    data.to_parquet(str(output_path))

                return {
                    "filepath": str(filepath),
                    "output": str(output_path),
                    "success": True,
                    "peaks": len(data.peaks),
                }
            else:
                return {
                    "filepath": str(filepath),
                    "success": True,
                    "data": data,
                    "peaks": len(data.peaks),
                }

        except Exception as e:
            return {
                "filepath": str(filepath),
                "success": False,
                "error": str(e),
            }

    def process_directory(
        self,
        directory: Path,
        pattern: str = "*",
        output_dir: Optional[Path] = None,
        output_format: str = "csv",
        progress_callback: Optional[Callable] = None,
    ) -> Dict[str, any]:
        """
        Process all files in a directory matching pattern.

        Args:
            directory: Directory to search
            pattern: File pattern (e.g., "*.arw")
            output_dir: Output directory
            output_format: Output format
            progress_callback: Progress callback

        Returns:
            Processing results
        """
        # Find matching files
        files = [Path(f) for f in glob.glob(str(directory / pattern))]

        if not files:
            logger.warning(f"No files found matching pattern '{pattern}' in {directory}")
            return {
                "success": [],
                "errors": [],
                "total": 0,
            }

        return self.process_files(
            files,
            output_dir=output_dir,
            output_format=output_format,
            progress_callback=progress_callback,
        )


# Convenience function
def batch_parse_async(
    filepaths: List[Path],
    output_dir: Optional[Path] = None,
    output_format: str = "csv",
    max_workers: int = 4,
    fail_fast: bool = False,
) -> Dict[str, any]:
    """
    High-level batch parsing function.

    Args:
        filepaths: Files to parse
        output_dir: Output directory
        output_format: Output format
        max_workers: Number of parallel workers
        fail_fast: Stop on first error

    Returns:
        Results dictionary

    Example:
        >>> files = [Path("sample1.arw"), Path("sample2.arw")]
        >>> results = batch_parse_async(files, output_dir=Path("./parsed"))
        >>> print(f"Parsed {len(results['success'])} files")
    """
    processor = BatchProcessor(max_workers=max_workers, fail_fast=fail_fast)
    return processor.process_files(filepaths, output_dir, output_format)

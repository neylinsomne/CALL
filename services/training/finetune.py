"""
F5-TTS Fine-tuning Script
Fine-tune F5-TTS Spanish model on custom voice data
"""

import os
import json
import click
from pathlib import Path
from datetime import datetime

import torch
import yaml
from torch.utils.data import Dataset, DataLoader
from torch.utils.tensorboard import SummaryWriter
import soundfile as sf
from tqdm import tqdm


# ===========================================
# Configuration
# ===========================================
DEFAULT_CONFIG = {
    "model": {
        "base_model": "jpgallegoar/F5-Spanish",
        "freeze_encoder": True,
        "freeze_decoder_layers": 8  # Freeze first N layers
    },
    "training": {
        "batch_size": 4,
        "learning_rate": 1e-5,
        "epochs": 100,
        "warmup_steps": 1000,
        "gradient_accumulation": 4,
        "max_grad_norm": 1.0,
        "save_every": 10,  # Save checkpoint every N epochs
        "eval_every": 5    # Evaluate every N epochs
    },
    "data": {
        "sample_rate": 24000,
        "max_duration": 15.0,
        "min_duration": 3.0
    }
}


# ===========================================
# Dataset
# ===========================================
class TTSDataset(Dataset):
    """Dataset for TTS fine-tuning"""
    
    def __init__(self, data_dir: str, metadata_file: str = "metadata.json"):
        self.data_dir = Path(data_dir)
        
        # Load metadata
        with open(self.data_dir / metadata_file, "r", encoding="utf-8") as f:
            self.metadata = json.load(f)
        
        print(f"Loaded {len(self.metadata)} samples")
    
    def __len__(self):
        return len(self.metadata)
    
    def __getitem__(self, idx):
        item = self.metadata[idx]
        
        # Load audio
        audio_path = self.data_dir / item["audio_file"]
        audio, sr = sf.read(str(audio_path))
        
        return {
            "audio": torch.tensor(audio, dtype=torch.float32),
            "text": item["text"],
            "duration": item["duration"]
        }


def collate_fn(batch):
    """Custom collate function for variable length audio"""
    # Pad audio to max length in batch
    max_len = max(item["audio"].shape[0] for item in batch)
    
    audio_padded = []
    audio_lens = []
    texts = []
    
    for item in batch:
        audio = item["audio"]
        audio_lens.append(len(audio))
        
        # Pad
        pad_len = max_len - len(audio)
        if pad_len > 0:
            audio = torch.nn.functional.pad(audio, (0, pad_len))
        audio_padded.append(audio)
        texts.append(item["text"])
    
    return {
        "audio": torch.stack(audio_padded),
        "audio_lens": torch.tensor(audio_lens),
        "texts": texts
    }


# ===========================================
# Training Functions
# ===========================================
def load_base_model(model_name: str, device: str):
    """Load the base F5-TTS model"""
    try:
        from f5_tts.api import F5TTS
        model = F5TTS(device=device)
        return model
    except ImportError:
        from f5_tts.infer.utils_infer import load_model
        model = load_model(model_name, device=device)
        return model


def freeze_layers(model, config: dict):
    """Freeze specified layers for fine-tuning"""
    if config["model"]["freeze_encoder"]:
        for param in model.encoder.parameters():
            param.requires_grad = False
        print("Encoder frozen")
    
    # Freeze first N decoder layers
    freeze_n = config["model"]["freeze_decoder_layers"]
    if hasattr(model, "decoder") and freeze_n > 0:
        for i, layer in enumerate(model.decoder.layers[:freeze_n]):
            for param in layer.parameters():
                param.requires_grad = False
        print(f"Frozen first {freeze_n} decoder layers")
    
    # Count trainable parameters
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    total = sum(p.numel() for p in model.parameters())
    print(f"Trainable parameters: {trainable:,} / {total:,} ({100*trainable/total:.1f}%)")


def train_epoch(model, dataloader, optimizer, scheduler, device, config):
    """Train for one epoch"""
    model.train()
    total_loss = 0
    
    progress = tqdm(dataloader, desc="Training")
    for batch_idx, batch in enumerate(progress):
        audio = batch["audio"].to(device)
        audio_lens = batch["audio_lens"].to(device)
        texts = batch["texts"]
        
        # Forward pass (implementation depends on F5-TTS internals)
        # This is a placeholder - actual implementation needs F5-TTS training API
        loss = torch.tensor(0.0, device=device, requires_grad=True)  # Placeholder
        
        # Backward pass
        loss = loss / config["training"]["gradient_accumulation"]
        loss.backward()
        
        if (batch_idx + 1) % config["training"]["gradient_accumulation"] == 0:
            torch.nn.utils.clip_grad_norm_(
                model.parameters(), 
                config["training"]["max_grad_norm"]
            )
            optimizer.step()
            scheduler.step()
            optimizer.zero_grad()
        
        total_loss += loss.item()
        progress.set_postfix({"loss": loss.item()})
    
    return total_loss / len(dataloader)


def evaluate(model, dataloader, device):
    """Evaluate model"""
    model.eval()
    total_loss = 0
    
    with torch.no_grad():
        for batch in dataloader:
            audio = batch["audio"].to(device)
            texts = batch["texts"]
            # Placeholder evaluation
            loss = torch.tensor(0.0)
            total_loss += loss.item()
    
    return total_loss / len(dataloader)


def save_checkpoint(model, optimizer, scheduler, epoch, loss, output_dir):
    """Save training checkpoint"""
    checkpoint_path = Path(output_dir) / f"checkpoint_epoch_{epoch}.pt"
    
    torch.save({
        "epoch": epoch,
        "model_state_dict": model.state_dict() if hasattr(model, 'state_dict') else None,
        "optimizer_state_dict": optimizer.state_dict(),
        "scheduler_state_dict": scheduler.state_dict(),
        "loss": loss
    }, checkpoint_path)
    
    print(f"Saved checkpoint: {checkpoint_path}")


# ===========================================
# Main Training Loop
# ===========================================
def train(
    data_dir: str,
    output_dir: str,
    config: dict,
    resume_from: str = None
):
    """Main training function"""
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {device}")
    
    # Setup output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Save config
    config_path = output_path / "config.yaml"
    with open(config_path, "w") as f:
        yaml.dump(config, f)
    
    # Initialize tensorboard
    writer = SummaryWriter(output_path / "logs")
    
    # Load dataset
    print("Loading dataset...")
    dataset = TTSDataset(data_dir)
    
    # Split into train/val
    train_size = int(0.9 * len(dataset))
    val_size = len(dataset) - train_size
    train_dataset, val_dataset = torch.utils.data.random_split(
        dataset, [train_size, val_size]
    )
    
    train_loader = DataLoader(
        train_dataset,
        batch_size=config["training"]["batch_size"],
        shuffle=True,
        collate_fn=collate_fn,
        num_workers=4
    )
    
    val_loader = DataLoader(
        val_dataset,
        batch_size=config["training"]["batch_size"],
        shuffle=False,
        collate_fn=collate_fn,
        num_workers=2
    )
    
    # Load model
    print("Loading model...")
    model = load_base_model(config["model"]["base_model"], device)
    freeze_layers(model, config)
    
    # Optimizer and scheduler
    optimizer = torch.optim.AdamW(
        filter(lambda p: p.requires_grad, model.parameters()),
        lr=config["training"]["learning_rate"]
    )
    
    total_steps = len(train_loader) * config["training"]["epochs"]
    scheduler = torch.optim.lr_scheduler.OneCycleLR(
        optimizer,
        max_lr=config["training"]["learning_rate"],
        total_steps=total_steps,
        pct_start=config["training"]["warmup_steps"] / total_steps
    )
    
    # Resume from checkpoint
    start_epoch = 0
    if resume_from:
        print(f"Resuming from {resume_from}")
        checkpoint = torch.load(resume_from)
        if checkpoint.get("model_state_dict"):
            model.load_state_dict(checkpoint["model_state_dict"])
        optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
        scheduler.load_state_dict(checkpoint["scheduler_state_dict"])
        start_epoch = checkpoint["epoch"] + 1
    
    # Training loop
    print(f"\nStarting training for {config['training']['epochs']} epochs")
    print(f"Train samples: {len(train_dataset)}, Val samples: {len(val_dataset)}")
    
    best_val_loss = float("inf")
    
    for epoch in range(start_epoch, config["training"]["epochs"]):
        print(f"\nEpoch {epoch + 1}/{config['training']['epochs']}")
        
        # Train
        train_loss = train_epoch(
            model, train_loader, optimizer, scheduler, device, config
        )
        writer.add_scalar("Loss/train", train_loss, epoch)
        
        # Evaluate
        if (epoch + 1) % config["training"]["eval_every"] == 0:
            val_loss = evaluate(model, val_loader, device)
            writer.add_scalar("Loss/val", val_loss, epoch)
            print(f"Train loss: {train_loss:.4f}, Val loss: {val_loss:.4f}")
            
            if val_loss < best_val_loss:
                best_val_loss = val_loss
                save_checkpoint(
                    model, optimizer, scheduler, epoch, val_loss,
                    output_dir
                )
                # Save best model
                best_path = output_path / "best_model.pt"
                torch.save(model.state_dict() if hasattr(model, 'state_dict') else model, best_path)
        
        # Regular checkpoint
        if (epoch + 1) % config["training"]["save_every"] == 0:
            save_checkpoint(
                model, optimizer, scheduler, epoch, train_loss,
                output_dir
            )
    
    writer.close()
    print(f"\nTraining complete! Best model saved to {output_path / 'best_model.pt'}")


# ===========================================
# CLI
# ===========================================
@click.command()
@click.option(
    '--data', '-d', 'data_dir',
    required=True,
    type=click.Path(exists=True),
    help='Directory with prepared training data'
)
@click.option(
    '--output', '-o', 'output_dir',
    required=True,
    type=click.Path(),
    help='Output directory for checkpoints'
)
@click.option(
    '--config', '-c', 'config_file',
    type=click.Path(exists=True),
    help='Config file (YAML)'
)
@click.option(
    '--resume', '-r', 'resume_from',
    type=click.Path(exists=True),
    help='Resume from checkpoint'
)
@click.option(
    '--epochs', '-e',
    type=int,
    default=None,
    help='Override number of epochs'
)
@click.option(
    '--batch-size', '-b',
    type=int,
    default=None,
    help='Override batch size'
)
@click.option(
    '--lr',
    type=float,
    default=None,
    help='Override learning rate'
)
def main(
    data_dir: str,
    output_dir: str,
    config_file: str,
    resume_from: str,
    epochs: int,
    batch_size: int,
    lr: float
):
    """
    Fine-tune F5-TTS Spanish model on custom voice data
    
    Example:
        python finetune.py -d ./data -o ./checkpoints -e 50
    """
    # Load config
    if config_file:
        with open(config_file, "r") as f:
            config = yaml.safe_load(f)
    else:
        config = DEFAULT_CONFIG.copy()
    
    # Override from CLI
    if epochs:
        config["training"]["epochs"] = epochs
    if batch_size:
        config["training"]["batch_size"] = batch_size
    if lr:
        config["training"]["learning_rate"] = lr
    
    # Run training
    train(data_dir, output_dir, config, resume_from)


if __name__ == "__main__":
    main()

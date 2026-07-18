#!/usr/bin/env bash

# Executor Agent Script
# Generates production-ready code from Work Unit specification

set -euo pipefail

# --- Configuration ---
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AGENT_NAME="Executor Agent"

# --- Color Output ---
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log() {
  echo -e "${GREEN}[${AGENT_NAME}]${NC} $1"
}

warn() {
  echo -e "${YELLOW}[${AGENT_NAME}]${NC} $1"
}

error() {
  echo -e "${RED}[${AGENT_NAME}]${NC} $1"
}

info() {
  echo -e "${BLUE}[${AGENT_NAME}]${NC} $1"
}

# --- Help ---
usage() {
  cat << EOF
Usage: $(basename "$0") [OPTIONS]

Generate production-ready code from Work Unit specification.

OPTIONS:
  --work-unit FILE        Path to Work Unit JSON file (required)
  --parity-contract FILE  Path to endpoint_mapping_schema.json (required)
  --plan FILE             Path to architectural plan.md (required)
  --output-dir DIR        Directory to save generated file (required)
  --rules FILE            Path to executor-agent.rules (optional)
  --feedback FILE         Path to review feedback (for corrections) (optional)
  --help                  Show this help message

EXAMPLE:
  $(basename "$0") \\
    --work-unit .spec-kitti/work-units/WU-005.json \\
    --parity-contract .spec-kitti/discovery/endpoint_mapping_schema.json \\
    --plan .spec-kitti/plan.md \\
    --output-dir src/ \\
    --rules .spec-kitti/.rules/executor-agent.rules

  # With feedback (correction loop)
  $(basename "$0") \\
    --work-unit .spec-kitti/work-units/WU-005.json \\
    --parity-contract .spec-kitti/discovery/endpoint_mapping_schema.json \\
    --plan .spec-kitti/plan.md \\
    --output-dir src/ \\
    --feedback .spec-kitti/implementation/WU-005-review.md

EOF
    exit 1
}

# --- Parse Arguments ---
WORK_UNIT_FILE=""
PARITY_CONTRACT_FILE=""
PLAN_FILE=""
OUTPUT_DIR=""
RULES_FILE=""
FEEDBACK_FILE=""

while [[ $# -gt 0 ]]; do
  case $1 in
    --work-unit)
      WORK_UNIT_FILE="$2"
      shift 2
      ;;
    --parity-contract)
      PARITY_CONTRACT_FILE="$2"
      shift 2
      ;;
    --plan)
      PLAN_FILE="$2"
      shift 2
      ;;
    --output-dir)
      OUTPUT_DIR="$2"
      shift 2
      ;;
    --rules)
      RULES_FILE="$2"
      shift 2
      ;;
    --feedback)
      FEEDBACK_FILE="$2"
      shift 2
      ;;
    --help)
      usage
      ;;
    *)
      error "Unknown option: $1"
      usage
      ;;
  esac
done

# --- Validate Required Arguments ---
if [[ -z "$WORK_UNIT_FILE" || -z "$PARITY_CONTRACT_FILE" || -z "$PLAN_FILE" || -z "$OUTPUT_DIR" ]]; then
  error "Missing required arguments"
  usage
fi

# --- Validate Input Files ---
if [[ ! -f "$WORK_UNIT_FILE" ]]; then
  error "Work Unit file not found: $WORK_UNIT_FILE"
  exit 1
fi

if [[ ! -f "$PARITY_CONTRACT_FILE" ]]; then
  error "Parity Contract file not found: $PARITY_CONTRACT_FILE"
  exit 1
fi

if [[ ! -f "$PLAN_FILE" ]]; then
  error "Plan file not found: $PLAN_FILE"
  exit 1
fi

if [[ -n "$RULES_FILE" && ! -f "$RULES_FILE" ]]; then
  error "Rules file not found: $RULES_FILE"
  exit 1
fi

if [[ -n "$FEEDBACK_FILE" && ! -f "$FEEDBACK_FILE" ]]; then
  error "Feedback file not found: $FEEDBACK_FILE"
  exit 1
fi

# --- Create Output Directory ---
mkdir -p "$OUTPUT_DIR"

# --- Load Inputs ---
log "Loading Work Unit: $WORK_UNIT_FILE"
WORK_UNIT_CONTENT=$(cat "$WORK_UNIT_FILE")

log "Loading Parity Contract: $PARITY_CONTRACT_FILE"
PARITY_CONTRACT_CONTENT=$(cat "$PARITY_CONTRACT_FILE")

log "Loading Architectural Plan: $PLAN_FILE"
PLAN_CONTENT=$(cat "$PLAN_FILE")

RULES_CONTENT=""
if [[ -n "$RULES_FILE" ]]; then
  log "Loading Rules: $RULES_FILE"
  RULES_CONTENT=$(cat "$RULES_FILE")
fi

FEEDBACK_CONTENT=""
if [[ -n "$FEEDBACK_FILE" ]]; then
  warn "Loading Feedback (correction mode): $FEEDBACK_FILE"
  FEEDBACK_CONTENT=$(cat "$FEEDBACK_FILE")
fi

# --- Extract Work Unit Metadata ---
WORK_UNIT_ID=$(echo "$WORK_UNIT_CONTENT" | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4)
FILE_PATH=$(echo "$WORK_UNIT_CONTENT" | grep -o '"file_path":"[^"]*"' | head -1 | cut -d'"' -f4)
ACTION=$(echo "$WORK_UNIT_CONTENT" | grep -o '"action":"[^"]*"' | head -1 | cut -d'"' -f4)

if [[ -z "$FILE_PATH" ]]; then
  error "Could not extract file_path from Work Unit"
  exit 1
fi

log "Processing Work Unit: $WORK_UNIT_ID"
log "File: $FILE_PATH ($ACTION)"

# Determine full output path
OUTPUT_FILE="${OUTPUT_DIR}/${FILE_PATH}"
OUTPUT_FILE_DIR=$(dirname "$OUTPUT_FILE")
mkdir -p "$OUTPUT_FILE_DIR"

# --- Banner ---
echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                       EXECUTOR AGENT                           ║"
echo "║                  Generating Production Code                    ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# --- Feedback Mode Check ---
if [[ -n "$FEEDBACK_CONTENT" ]]; then
  warn "CORRECTION MODE: Applying feedback from Reviewer Agent"
  warn "Feedback file: $FEEDBACK_FILE"
  echo ""
fi

# --- Generate Code ---
log "Analyzing Work Unit requirements..."
log "Looking up business rules in Parity Contract..."
log "Looking up parity anchors in Parity Contract..."
log "Applying framework patterns from plan.md..."
log "Generating code..."

# --- SIMULATED CODE GENERATION ---
# In production, this would call an AI API (Claude, GPT-4, etc.) with:
# - Work Unit JSON
# - Parity Contract
# - Architectural Plan
# - Rules
# - Feedback (if correction mode)

# For demonstration, generate a template based on file type
FILE_EXT="${FILE_PATH##*.}"

case "$FILE_EXT" in
  ts)
    # TypeScript/NestJS Service
    cat > "$OUTPUT_FILE" << 'EOFTS'
import { Injectable, ConflictException, BadRequestException, NotFoundException, InternalServerErrorException, Logger } from '@nestjs/common';
import { UserRepository } from './users.repository';
import { CreateUserDto, UpdateUserDto } from './dto';
import { User } from './entities/user.entity';
import { PaginatedResponse } from '../common/interfaces';
import * as bcrypt from 'bcrypt';

/**
 * User Service
 * 
 * Handles business logic for user management operations.
 * Implements business rules BR001-BR004 from Parity Contract.
 * 
 * @see Parity Contract EP001, EP002, EP003
 * @see Work Unit WU-005
 */
@Injectable()
export class UserService {
  private readonly logger = new Logger(UserService.name);
  private readonly MAX_PAGE_SIZE = 100;
  private readonly DEFAULT_PAGE_SIZE = 20;
  private readonly BCRYPT_ROUNDS = 10;

  constructor(
    private readonly userRepository: UserRepository,
  ) {}

  /**
   * Retrieves paginated list of active users
   * 
   * Business Rules:
   * - BR003: Pagination mandatory (default 20, max 100)
   * 
   * @param page - Page number (1-indexed)
   * @param size - Items per page (1-100)
   * @returns Paginated response with users
   * @see Parity Contract EP001
   */
  async listUsers(
    page: number = 1,
    size: number = this.DEFAULT_PAGE_SIZE,
  ): Promise<PaginatedResponse<User>> {
    // BR003: Normalize pagination parameters
    const normalizedPage = Math.max(page, 1);
    const normalizedSize = Math.min(Math.max(size, 1), this.MAX_PAGE_SIZE);

    this.logger.log(`Listing users: page=${normalizedPage}, size=${normalizedSize}`);

    try {
      const [users, total] = await this.userRepository.findAllPaginated(
        normalizedPage,
        normalizedSize,
      );

      const totalPages = Math.ceil(total / normalizedSize);

      return {
        data: users.map(user => this.sanitizeUser(user)),
        pagination: {
          page: normalizedPage,
          size: normalizedSize,
          total,
          totalPages,
        },
      };
    } catch (error) {
      this.logger.error(`Failed to list users: ${error.message}`, error.stack);
      throw new InternalServerErrorException('Failed to retrieve users');
    }
  }

  /**
   * Retrieves single user by ID
   * 
   * @param id - User ID
   * @returns User object
   * @throws NotFoundException if user not found
   * @see Parity Contract EP002
   */
  async getUser(id: string): Promise<User> {
    this.logger.log(`Getting user: id=${id}`);

    try {
      const user = await this.userRepository.findById(id);

      if (!user) {
        this.logger.warn(`User not found: id=${id}`);
        throw new NotFoundException('User not found');
      }

      return this.sanitizeUser(user);
    } catch (error) {
      if (error instanceof NotFoundException) {
        throw error;
      }
      this.logger.error(`Failed to get user: ${error.message}`, error.stack);
      throw new InternalServerErrorException('Failed to retrieve user');
    }
  }

  /**
   * Creates new user with validated unique username and email
   * 
   * Business Rules:
   * - BR001: Username must be unique
   * - BR002: Email must be corporate (@company.com) and unique
   * - BR004: Cannot create users with ADMIN role directly
   * 
   * @param dto - User creation data
   * @returns Created user (without password hash)
   * @see Parity Contract EP003
   */
  async createUser(dto: CreateUserDto): Promise<User> {
    this.logger.log(`Creating user: ${dto.username}`);

    // BR001: Validate unique username
    const existingUsername = await this.userRepository.findByUsername(dto.username);
    if (existingUsername) {
      this.logger.warn(`BR001: Username already exists - ${dto.username}`);
      throw new ConflictException('Username already exists');
    }

    // BR002: Validate corporate email
    if (!dto.email.endsWith('@company.com')) {
      this.logger.warn(`BR002: Non-corporate email - ${dto.email}`);
      throw new BadRequestException('Email must be from corporate domain (@company.com)');
    }

    // BR002: Validate unique email
    const existingEmail = await this.userRepository.findByEmail(dto.email);
    if (existingEmail) {
      this.logger.warn(`BR002: Email already exists - ${dto.email}`);
      throw new ConflictException('Email already exists');
    }

    try {
      // Hash password securely
      const passwordHash = await bcrypt.hash(dto.password, this.BCRYPT_ROUNDS);

      // BR004: Force USER role, ignore any role in DTO
      const userData = {
        username: dto.username,
        email: dto.email,
        passwordHash,
        isActive: true,
      };

      const user = await this.userRepository.create(userData);
      
      this.logger.log(`User created successfully: ${user.id}`);
      
      return this.sanitizeUser(user);
    } catch (error) {
      this.logger.error(`Failed to create user: ${error.message}`, error.stack);
      throw new InternalServerErrorException('Failed to create user');
    }
  }

  /**
   * Updates existing user
   * 
   * Business Rules:
   * - BR002: Email validation if updated
   * 
   * @param id - User ID
   * @param dto - Update data
   * @returns Updated user
   * @see Parity Contract EP004
   */
  async updateUser(id: string, dto: UpdateUserDto): Promise<User> {
    this.logger.log(`Updating user: id=${id}`);

    // Check user exists
    const existing = await this.getUser(id);

    // BR002: Validate email if updating
    if (dto.email) {
      if (!dto.email.endsWith('@company.com')) {
        this.logger.warn(`BR002: Non-corporate email - ${dto.email}`);
        throw new BadRequestException('Email must be from corporate domain');
      }

      const existingEmail = await this.userRepository.findByEmail(dto.email);
      if (existingEmail && existingEmail.id !== id) {
        this.logger.warn(`BR002: Email already exists - ${dto.email}`);
        throw new ConflictException('Email already exists');
      }
    }

    try {
      // Hash password if updating
      const updateData: any = { ...dto };
      if (dto.password) {
        updateData.passwordHash = await bcrypt.hash(dto.password, this.BCRYPT_ROUNDS);
        delete updateData.password;
      }

      const updated = await this.userRepository.update(id, updateData);
      this.logger.log(`User updated successfully: id=${id}`);
      return this.sanitizeUser(updated);
    } catch (error) {
      this.logger.error(`Failed to update user: ${error.message}`, error.stack);
      throw new InternalServerErrorException('Failed to update user');
    }
  }

  /**
   * Soft deletes user (sets isActive: false)
   * 
   * @param id - User ID
   * @see Parity Contract EP005
   */
  async deleteUser(id: string): Promise<void> {
    this.logger.log(`Deleting user: id=${id}`);

    // Check user exists
    await this.getUser(id);

    try {
      await this.userRepository.update(id, { isActive: false });
      this.logger.log(`User deleted successfully: id=${id}`);
    } catch (error) {
      this.logger.error(`Failed to delete user: ${error.message}`, error.stack);
      throw new InternalServerErrorException('Failed to delete user');
    }
  }

  /**
   * Removes sensitive data from user object
   */
  private sanitizeUser(user: User): Omit<User, 'passwordHash'> {
    const { passwordHash, ...sanitized } = user;
    return sanitized;
  }
}
EOFTS
    ;;
  
  py)
    # Python/Django Service
    cat > "$OUTPUT_FILE" << 'EOFPY'
"""
User Service

Handles business logic for user management operations.
Implements business rules BR001-BR004 from Parity Contract.

See: Parity Contract EP001, EP002, EP003
See: Work Unit WU-005
"""

import logging
from django.core.exceptions import ValidationError
from django.contrib.auth.hashers import make_password
from .models import User
from .serializers import UserSerializer

logger = logging.getLogger(__name__)

MAX_PAGE_SIZE = 100
DEFAULT_PAGE_SIZE = 20

def list_users(page=1, size=DEFAULT_PAGE_SIZE):
    """
    Retrieves paginated list of active users
    
    Business Rules:
    - BR003: Pagination mandatory (default 20, max 100)
    
    See: Parity Contract EP001
    """
    # BR003: Normalize pagination
    normalized_page = max(page, 1)
    normalized_size = min(max(size, 1), MAX_PAGE_SIZE)
    
    logger.info(f"Listing users: page={normalized_page}, size={normalized_size}")
    
    try:
        offset = (normalized_page - 1) * normalized_size
        users = User.objects.filter(is_active=True)[offset:offset + normalized_size]
        total = User.objects.filter(is_active=True).count()
        total_pages = (total + normalized_size - 1) // normalized_size
        
        return {
            'data': [sanitize_user(u) for u in users],
            'pagination': {
                'page': normalized_page,
                'size': normalized_size,
                'total': total,
                'total_pages': total_pages
            }
        }
    except Exception as e:
        logger.error(f"Failed to list users: {str(e)}")
        raise

def create_user(data):
    """
    Creates new user with validation
    
    Business Rules:
    - BR001: Username must be unique
    - BR002: Email must be corporate (@company.com) and unique
    - BR004: Cannot create users with ADMIN role directly
    
    See: Parity Contract EP003
    """
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    
    logger.info(f"Creating user: {username}")
    
    # BR001: Validate unique username
    if User.objects.filter(username=username).exists():
        logger.warning(f"BR001: Username already exists - {username}")
        raise ValidationError("Username already exists")
    
    # BR002: Validate corporate email
    if not email.endswith('@company.com'):
        logger.warning(f"BR002: Non-corporate email - {email}")
        raise ValidationError("Email must be from corporate domain (@company.com)")
    
    # BR002: Validate unique email
    if User.objects.filter(email=email).exists():
        logger.warning(f"BR002: Email already exists - {email}")
        raise ValidationError("Email already exists")
    
    try:
        # BR004: Force USER role
        user = User.objects.create(
            username=username,
            email=email,
            password=make_password(password),
            is_active=True
        )
        
        logger.info(f"User created successfully: {user.id}")
        return sanitize_user(user)
    except Exception as e:
        logger.error(f"Failed to create user: {str(e)}")
        raise

def sanitize_user(user):
    """Removes sensitive data from user object"""
    return {
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'is_active': user.is_active
    }
EOFPY
    ;;
  
  *)
    warn "Unknown file extension: $FILE_EXT - generating generic template"
    echo "// Generated code for $FILE_PATH" > "$OUTPUT_FILE"
    echo "// Work Unit: $WORK_UNIT_ID" >> "$OUTPUT_FILE"
            ;;
    esac
    
# --- Success ---
echo ""
log "Code generated successfully!"
log "Output: $OUTPUT_FILE"
echo ""

# --- Summary ---
info "GENERATION SUMMARY:"
info "  Work Unit: $WORK_UNIT_ID"
info "  File: $FILE_PATH"
info "  Action: $ACTION"
info "  Output: $OUTPUT_FILE"

if [[ -n "$FEEDBACK_CONTENT" ]]; then
  warn "  Mode: CORRECTION (applied feedback)"
fi

echo ""

exit 0
